package globalwb.endpoint;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;

import javax.servlet.http.HttpServletRequest;
import javax.ws.rs.Consumes;
import javax.ws.rs.DELETE;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.Response.Status;

import org.glassfish.jersey.media.multipart.FormDataContentDisposition;
import org.glassfish.jersey.media.multipart.FormDataParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import globalwb.service.ImageService;

@Component
@Path("/images")
public class ImageEndpoint {

	private ImageService imageService;
	
	@Autowired
	public ImageEndpoint(ImageService imageService) {
		this.imageService = imageService;
	}
	
	@GET
	@Path("/merged")
	@Produces("image/*")
	public Response getMerged() {
		
		File file = null;
		
		file = imageService.getMergedImageOrNull();
		
		if (file == null) {
			return Response.status(Status.NOT_FOUND)
					.header("Access-Control-Allow-Origin", "*")
					.header("Access-Control-Allow-Methods", "GET, POST, DELETE, PUT")
					.allow("OPTIONS")
					.build();
		} else {
			String mimeType = "image/png";
			return Response.ok(file, mimeType)
					.header("Access-Control-Allow-Origin", "*")
					.header("Access-Control-Allow-Methods", "GET, POST, DELETE, PUT")
					.allow("OPTIONS")
					.build();	
		}
		
		
	}
	
	@POST
	@Consumes(MediaType.MULTIPART_FORM_DATA)
	public Response upload(@FormDataParam("file") InputStream inputStream, 
			@FormDataParam("file") FormDataContentDisposition formDataContentDisposition, 
			@Context HttpServletRequest request) throws IOException {
		
		String remoteAddress = request.getRemoteAddr();
		
		
		System.out.println("remoteAddress: " + remoteAddress);
		imageService.save(inputStream, remoteAddress);
		
		
		return Response.created(null)
				.header("Access-Control-Allow-Origin", "*")
				.header("Access-Control-Allow-Methods", "GET, POST, DELETE, PUT")
				.allow("OPTIONS")
				.build();
	}
	
	@DELETE
	public Response deleteAll() {
		return null;
		
	}
}
