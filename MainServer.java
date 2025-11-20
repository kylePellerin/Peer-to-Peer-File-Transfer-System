import org.apache.xmlrpc.webserver.WebServer; 
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class MainServer {
  private static XmlRpcClient catalogClient;
  private static XmlRpcClient orderClient;
  private static HashMap<String, FileList> fileLists = new HashMap<String, FileList>(); // our file storage

  public static void main(String[] args) {
    if (args.length != 2) {
      System.out.println("Usage: java FrontEndServer [catalog_hostname] [order_hostname]");
      return;
    }
    String catalogHostname = args[0];
    String orderHostname = args[1];
    try {
      //setup the catalog client connection
      XmlRpcClientConfigImpl catalogConfig = new XmlRpcClientConfigImpl();
      catalogConfig.setServerURL(new java.net.URL("http://" + catalogHostname + ":8090")); 
      catalogClient = new XmlRpcClient();
      catalogClient.setConfig(catalogConfig);

      //setup the order client connection
      XmlRpcClientConfigImpl orderConfig = new XmlRpcClientConfigImpl();
      orderConfig.setServerURL(new java.net.URL("http://" + orderHostname + ":8091")); 
      orderClient = new XmlRpcClient();
      orderClient.setConfig(orderConfig);

      PropertyHandlerMapping phm = new PropertyHandlerMapping();
      XmlRpcServer xmlRpcServer;
      WebServer server = new WebServer(8089); // our port from project 1
      xmlRpcServer = server.getXmlRpcServer();
      phm.addHandler("Nile", FrontEndServer.class);
      xmlRpcServer.setHandlerMapping(phm);
      server.start();
      System.out.println("XML-RPC server started");
    } catch (Exception e) {
      System.err.println("Server exception: " + e);
    }
  }

  public Boolean buy(int item_number){
    try{
      List<Integer> params = new java.util.ArrayList<Integer>();
      params.add(item_number);
      Boolean result = (Boolean) orderClient.execute("Nile_Order.buy", params);
      return result;
    }catch(Exception e){
      System.err.println("Client exception: " + e);
      return false;
    }
  }
  
  public String lookup(int item_number){
    try{
      List<Integer> params = new java.util.ArrayList<Integer>();
      params.add(item_number);
      String result = (String) catalogClient.execute("Nile_Catalog.queryById", params);
      return result;
    }catch(Exception e){
      System.err.println("Client exception: " + e);
      return "Error: The lookup operation failed.";
    }
  }

  public List<Integer> search(String topic){
    try{
      List<String> params = new java.util.ArrayList<String>();
      params.add(topic);
      Object[] result = (Object[]) catalogClient.execute("Nile_Catalog.queryByTopic", params);
      List<Integer> idList = new java.util.ArrayList<Integer>();
      for(Object id : result){
        idList.add(Integer.parseInt((String) id));
      }
      return idList;
    }catch(Exception e){
      System.err.println("Client exception: " + e);
      return new ArrayList<Integer>();
    }
  }
}
