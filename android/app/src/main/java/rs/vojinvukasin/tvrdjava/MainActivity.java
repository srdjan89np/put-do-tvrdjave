package rs.vojinvukasin.tvrdjava;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.os.Handler;
import android.os.Looper;
import android.window.OnBackInvokedDispatcher;

import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.AdSize;
import com.google.android.gms.ads.AdView;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.RequestConfiguration;
import com.google.android.gms.ads.rewarded.RewardedAd;
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback;
import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.nearby.Nearby;
import com.google.android.gms.nearby.connection.AdvertisingOptions;
import com.google.android.gms.nearby.connection.ConnectionInfo;
import com.google.android.gms.nearby.connection.ConnectionLifecycleCallback;
import com.google.android.gms.nearby.connection.ConnectionResolution;
import com.google.android.gms.nearby.connection.ConnectionsClient;
import com.google.android.gms.nearby.connection.ConnectionsStatusCodes;
import com.google.android.gms.nearby.connection.DiscoveredEndpointInfo;
import com.google.android.gms.nearby.connection.DiscoveryOptions;
import com.google.android.gms.nearby.connection.EndpointDiscoveryCallback;
import com.google.android.gms.nearby.connection.Payload;
import com.google.android.gms.nearby.connection.PayloadCallback;
import com.google.android.gms.nearby.connection.PayloadTransferUpdate;
import com.google.android.gms.nearby.connection.Strategy;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Igrica "Put do Kraljeve tvrđave" u WebView-u, sa reklamnim banerom (AdMob) na dnu ekrana
 * i reklamom sa nagradom (dodatni život, samo kad je igrač izabere).
 * Igru igraju i deca, pa se sve reklame traže kao reklame za decu (bez personalizacije, ocena G).
 */
public class MainActivity extends Activity {

    private WebView web;
    private FrameLayout adBox;
    private AdView adView;
    private volatile RewardedAd rewarded;
    private boolean rewardedLoading = false;

    // Igra preko Blututa (Google Nearby Connections): telefoni u blizini, bez interneta.
    private static final String NET_SERVICE = "rs.vojinvukasin.tvrdjava.igra";
    private static final int NET_PERM_REQ = 77;
    private ConnectionsClient net;
    private final List<String> netPeers = new ArrayList<>();
    private String netPendingMode = null, netPendingName = null;
    private final Handler ui = new Handler(Looper.getMainLooper());

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window w = getWindow();
        w.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (Build.VERSION.SDK_INT >= 28) {
            w.getAttributes().layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#131833"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setTextZoom(100);
        web.setVerticalScrollBarEnabled(false);
        web.setHorizontalScrollBarEnabled(false);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());
        web.addJavascriptInterface(new AdsBridge(), "AndroidAds");
        web.addJavascriptInterface(new NetBridge(), "AndroidNet");

        // Igra gore, baner dole.
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#131833"));
        root.addView(web, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));
        adBox = new FrameLayout(this);
        root.addView(adBox, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        setContentView(root);
        hideSystemBars();

        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState);
        } else {
            web.loadUrl("file:///android_asset/index.html");
        }

        // Android 16 i noviji (targetSdk 36) ne šalju taster "nazad", nego ovaj poziv.
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::handleBack);
        }

        setUpAds();
    }

    /** Reklame za decu: bez personalizacije i samo sadržaj za sve uzraste (G). */
    private void setUpAds() {
        RequestConfiguration config = MobileAds.getRequestConfiguration().toBuilder()
                .setTagForChildDirectedTreatment(RequestConfiguration.TAG_FOR_CHILD_DIRECTED_TREATMENT_TRUE)
                .setTagForUnderAgeOfConsent(RequestConfiguration.TAG_FOR_UNDER_AGE_OF_CONSENT_TRUE)
                .setMaxAdContentRating(RequestConfiguration.MAX_AD_CONTENT_RATING_G)
                .build();
        MobileAds.setRequestConfiguration(config);
        new Thread(() -> MobileAds.initialize(this, status ->
                runOnUiThread(() -> { adBox.post(this::loadBanner); loadRewarded(); }))).start();
    }

    /** Reklama sa nagradom se učitava unapred, da bude spremna kad igrač ostane bez života. */
    private void loadRewarded() {
        if (rewarded != null || rewardedLoading || isFinishing()) return;
        rewardedLoading = true;
        RewardedAd.load(this, BuildConfig.ADMOB_REWARDED_ID, new AdRequest.Builder().build(),
                new RewardedAdLoadCallback() {
                    @Override
                    public void onAdLoaded(RewardedAd ad) {
                        rewarded = ad;
                        rewardedLoading = false;
                    }

                    @Override
                    public void onAdFailedToLoad(LoadAdError error) {
                        rewardedLoading = false;
                    }
                });
    }

    private void showRewarded() {
        RewardedAd ad = rewarded;
        if (ad == null) {
            sendReward(false);
            loadRewarded();
            return;
        }
        rewarded = null;
        final boolean[] earned = {false};
        ad.setFullScreenContentCallback(new FullScreenContentCallback() {
            @Override
            public void onAdDismissedFullScreenContent() {
                sendReward(earned[0]);
                hideSystemBars();
                loadRewarded();
            }

            @Override
            public void onAdFailedToShowFullScreenContent(AdError error) {
                sendReward(false);
                loadRewarded();
            }
        });
        ad.show(this, reward -> earned[0] = true);
    }

    private void sendReward(boolean ok) {
        web.evaluateJavascript("window.onRewardResult&&window.onRewardResult(" + ok + ")", null);
    }

    /** Most između igre (JavaScript) i AdMob-a. */
    private class AdsBridge {
        @JavascriptInterface
        public boolean ready() {
            return rewarded != null;
        }

        @JavascriptInterface
        public void show() {
            runOnUiThread(MainActivity.this::showRewarded);
        }
    }

    /** Prilagodljivi baner preko cele širine ekrana. */
    private void loadBanner() {
        if (isFinishing()) return;
        if (adView != null) {
            adBox.removeView(adView);
            adView.destroy();
        }
        adView = new AdView(this);
        adView.setAdUnitId(BuildConfig.ADMOB_BANNER_ID);
        DisplayMetrics dm = getResources().getDisplayMetrics();
        int widthPx = adBox.getWidth() > 0 ? adBox.getWidth() : dm.widthPixels;
        int widthDp = (int) (widthPx / dm.density);
        adView.setAdSize(AdSize.getCurrentOrientationAnchoredAdaptiveBannerAdSize(this, widthDp));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        lp.gravity = Gravity.CENTER_HORIZONTAL;
        adBox.addView(adView, lp);
        adView.loadAd(new AdRequest.Builder().build());
    }

    /* ---------- Igra preko Blututa ---------- */

    /** Radi na Androidu 13 i novijim (bez dozvole za lokaciju), uz Google Play usluge. */
    private boolean netAvailable() {
        return Build.VERSION.SDK_INT >= 33 && GoogleApiAvailability.getInstance()
                .isGooglePlayServicesAvailable(this) == ConnectionResult.SUCCESS;
    }

    private String[] netPermissions() {
        return new String[]{Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_ADVERTISE,
                Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.NEARBY_WIFI_DEVICES};
    }

    private boolean netHasPermissions() {
        for (String p : netPermissions())
            if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) return false;
        return true;
    }

    private void netEvent(String type, String id, String name, String data) {
        try {
            JSONObject o = new JSONObject();
            o.put("type", type);
            if (id != null) o.put("id", id);
            if (name != null) o.put("name", name);
            if (data != null) o.put("data", data);
            final String js = "window.onNet&&window.onNet(" + o + ")";
            ui.post(() -> web.evaluateJavascript(js, null));
        } catch (Exception ignored) {
        }
    }

    private final PayloadCallback netPayload = new PayloadCallback() {
        @Override
        public void onPayloadReceived(String id, Payload payload) {
            if (payload.getType() == Payload.Type.BYTES && payload.asBytes() != null)
                netEvent("message", id, null, new String(payload.asBytes(), StandardCharsets.UTF_8));
        }

        @Override
        public void onPayloadTransferUpdate(String id, PayloadTransferUpdate update) {
        }
    };

    private final ConnectionLifecycleCallback netLife = new ConnectionLifecycleCallback() {
        @Override
        public void onConnectionInitiated(String id, ConnectionInfo info) {
            net.acceptConnection(id, netPayload);
        }

        @Override
        public void onConnectionResult(String id, ConnectionResolution result) {
            if (result.getStatus().getStatusCode() == ConnectionsStatusCodes.STATUS_OK) {
                if (!netPeers.contains(id)) netPeers.add(id);
                if ("join".equals(netPendingMode)) net.stopDiscovery();
                netEvent("connected", id, null, null);
            } else {
                netEvent("failed", id, null, null);
            }
        }

        @Override
        public void onDisconnected(String id) {
            netPeers.remove(id);
            netEvent("disconnected", id, null, null);
        }
    };

    private final EndpointDiscoveryCallback netFound = new EndpointDiscoveryCallback() {
        @Override
        public void onEndpointFound(String id, DiscoveredEndpointInfo info) {
            netEvent("found", id, info.getEndpointName(), null);
        }

        @Override
        public void onEndpointLost(String id) {
            netEvent("lost", id, null, null);
        }
    };

    private void netStart(String mode, String name) {
        if (!netAvailable()) { netEvent("error", null, null, "unavailable"); return; }
        netPendingMode = mode;
        netPendingName = name;
        if (!netHasPermissions()) { requestPermissions(netPermissions(), NET_PERM_REQ); return; }
        if (net == null) net = Nearby.getConnectionsClient(this);
        netStopAll();
        netPendingMode = mode;
        if ("host".equals(mode)) {
            net.startAdvertising(name, NET_SERVICE, netLife,
                    new AdvertisingOptions.Builder().setStrategy(Strategy.P2P_STAR).build())
                    .addOnSuccessListener(v -> netEvent("ready", null, null, "host"))
                    .addOnFailureListener(e -> netEvent("error", null, null, "advertise"));
        } else {
            net.startDiscovery(NET_SERVICE, netFound,
                    new DiscoveryOptions.Builder().setStrategy(Strategy.P2P_STAR).build())
                    .addOnSuccessListener(v -> netEvent("ready", null, null, "join"))
                    .addOnFailureListener(e -> netEvent("error", null, null, "discover"));
        }
    }

    private void netStopAll() {
        if (net == null) return;
        net.stopAdvertising();
        net.stopDiscovery();
        net.stopAllEndpoints();
        netPeers.clear();
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        super.onRequestPermissionsResult(code, perms, results);
        if (code != NET_PERM_REQ) return;
        if (netHasPermissions() && netPendingMode != null) netStart(netPendingMode, netPendingName);
        else netEvent("error", null, null, "permission");
    }

    /** Most između igre (JavaScript) i Nearby veze. */
    private class NetBridge {
        @JavascriptInterface
        public boolean available() {
            return netAvailable();
        }

        @JavascriptInterface
        public void host(String name) {
            ui.post(() -> netStart("host", name));
        }

        @JavascriptInterface
        public void join(String name) {
            ui.post(() -> netStart("join", name));
        }

        @JavascriptInterface
        public void connect(String id, String name) {
            ui.post(() -> { if (net != null) net.requestConnection(name, id, netLife)
                    .addOnFailureListener(e -> netEvent("failed", id, null, null)); });
        }

        @JavascriptInterface
        public void stopFinding() {
            ui.post(() -> { if (net != null) { net.stopAdvertising(); net.stopDiscovery(); } });
        }

        @JavascriptInterface
        public void send(String id, String data) {
            ui.post(() -> {
                if (net == null || netPeers.isEmpty()) return;
                Payload p = Payload.fromBytes(data.getBytes(StandardCharsets.UTF_8));
                if ("*".equals(id)) net.sendPayload(new ArrayList<>(netPeers), p);
                else if (netPeers.contains(id)) net.sendPayload(id, p);
            });
        }

        @JavascriptInterface
        public void stop() {
            ui.post(MainActivity.this::netStopAll);
        }
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // Telefon je okrenut: baner se pravi ponovo za novu širinu.
        if (adView != null) adBox.post(this::loadBanner);
    }

    @SuppressWarnings("deprecation")
    private void hideSystemBars() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemBars();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }

    @Override
    protected void onPause() {
        if (adView != null) adView.pause();
        super.onPause();
        web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
        if (adView != null) adView.resume();
        hideSystemBars();
    }

    /** "Nazad" pauzira igru (kao taster P); kad je otvoren meni, izlazi iz aplikacije. */
    private void handleBack() {
        web.evaluateJavascript(
                "(function(){var c=document.getElementById('card');"
                        + "if(c&&c.hidden){window.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyP'}));return 'paused';}"
                        + "return 'menu';})()",
                result -> { if (result != null && result.contains("menu")) finish(); });
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        // Android 15 i stariji: dugme "nazad" stiže kao taster.
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            handleBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        netStopAll();
        if (adView != null) adView.destroy();
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
