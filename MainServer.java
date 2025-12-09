import org.apache.xmlrpc.webserver.WebServer;
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import java.net.URL;
import java.util.HashMap;
import java.util.Vector;

public class MainServer {
  private static HashMap<String, FileList> fileLists = new HashMap<String, FileList>(); 
  private static Set<String> blackList = new HashSet<String>();
  private static String backupServerIp = null;
  private static final int backupServerPort = 8642;
  private static final int mainPort = 8641;


  public static void main(String[] args) {
    try {
    if (args.length > 0) {
        mainPort = Integer.parseInt(args[0]);
    }
    if (args.length == 3) {
        backupServerIp = args[1];
        backupServerPort = Integer.parseInt(args[2]);
        System.out.println("Backup server set to " + backupServerIp + ":" + backupServerPort);
    }else {
        System.out.println("No backup server configured, running as a standalone.");
    }
    System.out.println("Attempting to start Server...");
    WebServer server = new WebServer(mainPort); 
    
    XmlRpcServer xmlRpcServer = server.getXmlRpcServer();
    PropertyHandlerMapping phm = new PropertyHandlerMapping();
    
    // This tells the server to make a new MainServer object for every request
    phm.addHandler("P2P", MainServer.class);
    
    xmlRpcServer.setHandlerMapping(phm);
    server.start();
    System.out.println("XML-RPC server started on " + mainPort);
    } catch (Exception e) {
      System.err.println("Server exception: " + e);
    }
  }

  public String register_files(String clientIp, Object[] fileList) {
        System.out.println("Register request from " + clientIp);

        synchronized(fileLists) { //update main 
            for (Object fileObj : fileList) {
                String filename = (String) fileObj;
                if (!fileLists.containsKey(filename)) {
                    fileLists.put(filename, new FileList());
                }
                fileLists.get(filename).addFile(clientIp);
            }
        }
        if (backupServerIp != null) { //if we have a backoup were gonna write to it
            try {
                System.out.println("Replicating to backup");
                XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
                config.setServerURL(new URL("http://" + backupServerIp + ":" + backupServerPort));
                XmlRpcClient client = new XmlRpcClient();
                client.setConfig(config);
                // call method on backup server
                Object[] params = new Object[]{clientIp, fileList};
                client.execute("P2P.register_files", params);
                System.out.println("Replication success.");
            } catch (Exception e) {
                System.out.println("Replication FAILED: " + e.getMessage());
                // don't crash just log because primary alive
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
                return new Vector<String>(); 
            }
        }
    }
}