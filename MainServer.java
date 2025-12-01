import org.apache.xmlrpc.webserver.WebServer; 
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import java.util.HashMap;
import java.util.Vector;

public class MainServer {
  private HashMap<String, FileList> fileLists = new HashMap<String, FileList>(); // our file storage

  public static void main(String[] args) {
    try {


      PropertyHandlerMapping phm = new PropertyHandlerMapping();
      XmlRpcServer xmlRpcServer;
      WebServer server = new WebServer(8089); // our port from project 1
      xmlRpcServer = server.getXmlRpcServer();
      phm.addHandler("P2P", MainServer.class);
      xmlRpcServer.setHandlerMapping(phm);
      server.start();
      System.out.println("XML-RPC server started");
    } catch (Exception e) {
      System.err.println("Server exception: " + e);
    }
  }

  public String register_files(String clientIp, Vector<String> fileList) {
        System.out.println("Register request from " + clientIp);
        
        synchronized(fileLists) {
            // Iterate through the array of files the client sent
            for (Object fileObj : fileList) {
                String filename = (String) fileObj;
                if (!fileLists.containsKey(filename)) {
                    fileLists.put(filename, new FileList());
                    System.out.println("   New file tracked: " + filename);
                }
                fileLists.get(filename).addFile(clientIp);
                System.out.println("   Added " + clientIp + " to " + filename);
            }
        }
        return "Files Registered";
    }
    

    public Vector<String> search_file(String filename) {
        System.out.println("Search request for: " + filename);
        
        synchronized(fileLists) {
            if (fileLists.containsKey(filename)) {
                return new Vector<String>(fileLists.get(filename).getFiles());
            } else {
                return new Vector<String>(); // Return empty list
            }
        }
    }
}

  