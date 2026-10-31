import com.android.aapt.Resources;
import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import java.nio.file.*;
/** Pretvara proto JSON u binarni protobuf (aapt.pb.ResourceTable ili aapt.pb.XmlNode). */
public class Json2Pb {
  public static void main(String[] a) throws Exception {
    Message.Builder b = a[0].equals("table") ? Resources.ResourceTable.newBuilder() : Resources.XmlNode.newBuilder();
    JsonFormat.parser().merge(new String(Files.readAllBytes(Paths.get(a[1])), "UTF-8"), b);
    Files.write(Paths.get(a[2]), b.build().toByteArray());
    System.out.println(JsonFormat.printer().print(b).length() + " ok " + a[2]);
  }
}
