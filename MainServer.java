import org.apache.xmlrpc.webserver.WebServer;
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import java.util.HashMap;
import java.util.Vector;

public class MainServer {
  // FIX 1: This MUST be static so the data survives between requests
  private static HashMap<String, FileList> fileLists = new HashMap<String, FileList>(); 

  public static void main(String[] args) {
    try {
      System.out.println("Attempting to start Server...");
      WebServer server = new WebServer(8089); 
      
      XmlRpcServer xmlRpcServer = server.getXmlRpcServer();
      PropertyHandlerMapping phm = new PropertyHandlerMapping();
      
      // This tells the server to make a new MainServer object for every request
      phm.addHandler("P2P", MainServer.class);
      
      xmlRpcServer.setHandlerMapping(phm);
      server.start();
      System.out.println("XML-RPC server started on 8089");
    } catch (Exception e) {
      System.err.println("Server exception: " + e);
    }
  }

  // FIX 2: Change Vector<String> to Object[] for better Python compatibility
  public String register_files(String clientIp, Object[] fileList) {
        System.out.println("Register request from " + clientIp);
        
        synchronized(fileLists) {
            for (Object fileObj : fileList) {
                String filename = (String) fileObj;
                
                // Create the file entry if it doesn't exist
                if (!fileLists.containsKey(filename)) {
                    fileLists.put(filename, new FileList());
                    System.out.println("   New file tracked: " + filename);
                }
                
                // Add the peer to the file entry
                // NOTE: Ensure your FileList.java has a method 'addPeer' or 'addFile'
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
                // Ensure FileList.java has a method 'getFiles' that returns a List or Vector
                return new Vector<String>(fileLists.get(filename).getFiles());
            } else {
                return new Vector<String>(); 
            }
        }
    }
}