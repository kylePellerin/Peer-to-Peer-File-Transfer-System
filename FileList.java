import java.util.ArrayList;
public class FileList {
    private ArrayList<String> files; // boolean for has file now we will ahve to change later to comply with partial files
    // stirng is ip and bool is has file or not 
    public FileList() {
        files = new ArrayList<String>(); 
    }

    private void addFile(String fileName) {
        files.add(fileName);
    }

    private void removeFile(String fileName) {
        files.remove(fileName);
    }

    private boolean hasFile(String fileName) {
        return files.contains(fileName);
    }

    private ArrayList<String> getFiles() {
        return files;
    }
}