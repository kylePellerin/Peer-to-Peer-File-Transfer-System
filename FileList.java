import java.util.HashMap;
public class FileList {
    private HashMap<String, Boolean> files; // boolean for has file now we will ahve to change later to comply with partial files
    // stirng is ip and bool is has file or not 
    public FileList() {
        files = new HashMap<String, Boolean>();
    }

    private void addFile(String fileName) {
        files.put(fileName, true);
    }

    private void updateFileStatus(String fileName, Boolean status) {
        if (files.containsKey(fileName)) {
            files.put(fileName, status);    
        }
    }

    private void removeFile(String fileName) {
        files.remove(fileName);
    }

    private boolean hasFile(String fileName) {
        return files.getOrDefault(fileName, false);
    }
}