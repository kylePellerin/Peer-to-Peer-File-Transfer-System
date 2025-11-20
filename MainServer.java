import org.apache.xmlrpc.webserver.WebServer; 
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class MainServer {
  private static HashMap<String, FileList> fileLists = new HashMap<String, FileList>(); // our file storage




  public static void main(String[] args) {
    try {
      //setup the catalog client connection

      //setup the order client connection

      PropertyHandlerMapping phm = new PropertyHandlerMapping();
      XmlRpcServer xmlRpcServer;
      WebServer server = new WebServer(8089); // our port from project 1
      xmlRpcServer = server.getXmlRpcServer();
      phm.addHandler("Main", MainServer.class);
      xmlRpcServer.setHandlerMapping(phm);
      server.start();
      System.out.println("XML-RPC server started");
    } catch (Exception e) {
      System.err.println("Server exception: " + e);
    }
  }
}

  