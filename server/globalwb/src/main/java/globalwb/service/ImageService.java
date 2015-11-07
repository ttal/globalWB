package globalwb.service;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.apache.commons.exec.CommandLine;
import org.apache.commons.exec.DefaultExecutor;
import org.apache.commons.io.FileUtils;

@Service
public class ImageService {

	private String USER_HOME = System.getProperty("user.home");
	
	@Value("${snapshotImage.path}")
	private String SNAPSHOT_IMAGE_PATH;
	
	@Value("${mergedImage.path}")
	private String MERGED_IMAGE_PATH;
	
	public void save(InputStream inputStream, String remoteAddress) throws IOException {
		String filename = remoteAddress.replaceAll("\\.", "_");
		File file = new File(USER_HOME + SNAPSHOT_IMAGE_PATH + "/" + filename + ".png");
		
		FileUtils.copyInputStreamToFile(inputStream, file);
		
		inputStream.close();
		
		System.out.println("saved");
		
		mergeImages();
	}
	
	public void mergeImages() throws IOException {
		
		File snapshotFolder = new File(USER_HOME + SNAPSHOT_IMAGE_PATH);
		File[] snapshotImages = snapshotFolder.listFiles();
		
		for (File file : snapshotImages) {
			System.out.println("file: " + file.getName());
		}
		
		if (snapshotImages.length == 1) {
			FileUtils.copyFile(snapshotImages[0], new File(USER_HOME + MERGED_IMAGE_PATH + "/merged-image.png"));
		} else {
			
			String line = "python " + USER_HOME + "/Code/python-script/merge_images.py " 
					+ USER_HOME + SNAPSHOT_IMAGE_PATH + "/" + snapshotImages[0].getName() + " "
					+ USER_HOME + SNAPSHOT_IMAGE_PATH + "/" + snapshotImages[1].getName() + " "
					+ USER_HOME + MERGED_IMAGE_PATH + "/merged-image.png";
			//String line = "AcroRd32.exe /p /h " + file.getAbsolutePath();
			CommandLine cmdLine = CommandLine.parse(line);
			DefaultExecutor executor = new DefaultExecutor();
			executor.setExitValue(1);
			int exitValue = executor.execute(cmdLine);
		}
	}
	
	public File getMergedImageOrNull() {
		
		File file = new File(USER_HOME + MERGED_IMAGE_PATH + "/merged-image.png");
		
		if (file.exists()) {
			return file;
		}
		
		return null;
	}
}
