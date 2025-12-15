import org.apache.xmlrpc.webserver.WebServer;
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import java.net.URL;
import java.util.HashMap;
import java.util.Vector;
import java.util.HashSet;
import java.util.*;
import java.util.ArrayList;
import java.util.Iterator;

public class MainServer {
  private static HashMap<String, FileList> fileLists = new HashMap<String, FileList>(); 
  private static HashSet<String> blackList = new HashSet<String>();
  private static String backupServerIp = null;
  private static int backupServerPort = 8642;
  private static int mainPort = 8641;


  public static void main(String[] args) {
    try {
    if (args.length > 0) {
        mainPort = Integer.parseInt(args[0]);
    }
    if (args.length == 3) {
        backupServerIp = args[1];
        backupServerPort = Integer.parseInt(args[2]);
        System.out.println("Backup server set to " + backupServerIp + ":" + backupServerPort);
        syncWithBackup(); //if backup has logs we need to get them in case of main restart
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

  private void notifyBackup(String methodName, Object[] params) {
      if (backupServerIp == null) {
          return;
      }
      try {
          System.out.println("Replicating " + methodName + " to backup...");
          
          XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
          config.setServerURL(new URL("http://" + backupServerIp + ":" + backupServerPort));
          
          XmlRpcClient client = new XmlRpcClient();
          client.setConfig(config);
          
          client.execute(methodName, params);
          
      } catch (Exception e) {
          // We print the method name so we know which action failed
          System.out.println("Backup Replication Failed (" + methodName + "): " + e.getMessage());
      }
  }

  private static void syncWithBackup() { //if the main goes down and backup logs stuff we need to update main when it comes back online so we call this
      try {
          System.out.println("Attempting to sync state from Backup...");
          XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
          config.setServerURL(new URL("http://" + backupServerIp + ":" + backupServerPort));
          XmlRpcClient client = new XmlRpcClient();
          client.setConfig(config);

          Object response = client.execute("P2P.get_all_files", new Object[]{});
          if (response instanceof Map) { //basically rebuild from the backups data strcutres
              Map<String, Object[]> rawFiles = (Map<String, Object[]>) response;
              synchronized(fileLists) {
                  for (String filename : rawFiles.keySet()) {
                      Object[] ips = rawFiles.get(filename);
                      FileList fl = new FileList();
                      for (Object ip : ips) {
                          fl.addFile((String)ip);
                      }
                      fileLists.put(filename, fl);
                  }
              }
              System.out.println("Synced " + rawFiles.size() + " files from backup.");
          }

          Object[] blockedUsers = (Object[]) client.execute("P2P.get_black_list", new Object[]{});
          synchronized(blackList) { //rebuild blacklist from backup
              for (Object ip : blockedUsers) {
                  blackList.add((String)ip);
              }
          }
          System.out.println("Synced " + blockedUsers.length + " blacklisted users from backup.");

      } catch (Exception e) {
          System.out.println("Sync Failed (Backup might be down or empty): " + e.getMessage());
          //if backup down or empty we just start as normal
      }
  }  
  public Map<String, Object[]> get_all_files() { //get all files from filelist for the sync method above
      System.out.println("Sync request received: Sending file list.");
      Map<String, Object[]> exportData = new HashMap<>();
      synchronized(fileLists) {
          for (String filename : fileLists.keySet()) {
              ArrayList<String> ips = fileLists.get(filename).getFiles();
              exportData.put(filename, ips.toArray());
          }
      }
      return exportData;
  }

  public Object[] get_black_list() { //get all blacklisted ips from blacklist for the sync method above
      System.out.println("Sync request received: Sending blacklist.");
      synchronized(blackList) {
          return blackList.toArray();
      }
  }
  private boolean isBlacklisted(String ip) { //check if ip is blacklisted
      synchronized(blackList) {
          return blackList.contains(ip);
      }
  }

  public String register_files(String clientIp, Object[] fileList) {
    if (isBlacklisted(clientIp)) {
            System.out.println("Blocked register request from blacklisted IP: " + clientIp);
            return "Error: You are blacklisted.";
        }
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
                notifyBackup("P2P.register_files", new Object[]{clientIp, fileList});
                System.out.println("Replication success.");
            } catch (Exception e) {
                System.out.println("Replication FAILED: " + e.getMessage());
                // don't crash just log because primary alive
            }
        }

        return "Files Registered";
    }
    
public String report_user(String badUserIp) {
        System.out.println("REPORT RECEIVED: User " + badUserIp + " has been reported.");
        
        synchronized(blackList) {
            if (!blackList.contains(badUserIp)) {
                blackList.add(badUserIp);
                System.out.println("User " + badUserIp + " added to blacklist.");
            }
        }

        if (backupServerIp != null) { 
            try {
                System.out.println("Replicating blacklist to backup...");
                notifyBackup("P2P.report_user", new Object[]{badUserIp});
                System.out.println("Blacklist Replication success.");
            } catch (Exception e) {
                System.out.println("Blacklist Replication FAILED: " + e.getMessage());
            }
        }
        
        return "User Blacklisted";
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

    public String unregister_client(String clientIp) {
        System.out.println("Unregister request from " + clientIp);
        
        synchronized(fileLists) {
            Iterator<Map.Entry<String, FileList>> it = fileLists.entrySet().iterator();
            
            while (it.hasNext()) {
                Map.Entry<String, FileList> entry = it.next();
                FileList fl = entry.getValue();
                fl.removeFile(clientIp); 
                if (fl.getFiles().isEmpty()) {
                    it.remove();
                }
            }
        }

        if (backupServerIp != null) { 
            try {
                System.out.println("Replicating unregister to backup...");
                notifyBackup("P2P.unregister_client", new Object[]{clientIp});
            } catch (Exception e) {
                System.out.println("Unregister Replication FAILED: " + e.getMessage());
            }
        }
        return "Client Unregistered";
    }
}