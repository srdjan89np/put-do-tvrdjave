package rs.vojinvukasin.tvrdjava;

import android.annotation.SuppressLint;
import android.app.Activity;
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
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.window.OnBackInvokedDispatcher;

import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.AdSize;
import com.google.android.gms.ads.AdView;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.RequestConfiguration;

/**
 * Igrica "Put do Kraljeve tvrđave" u WebView-u, sa reklamnim banerom (AdMob) na dnu ekrana.
 * Igru igraju i deca, pa se sve reklame traže kao reklame za decu (bez personalizacije, ocena G).
 */
public class MainActivity extends Activity {

    private WebView web;
    private FrameLayout adBox;
    private AdView adView;

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
                runOnUiThread(() -> adBox.post(this::loadBanner)))).start();
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
        if (adView != null) adView.destroy();
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
