package globalwb.config;

import javax.ws.rs.ApplicationPath;

import org.glassfish.jersey.media.multipart.MultiPartFeature;
import org.glassfish.jersey.server.ResourceConfig;
import org.springframework.context.annotation.Configuration;

import globalwb.endpoint.ImageEndpoint;

@Configuration
@ApplicationPath("/api")
public class JerseyConfig extends ResourceConfig {
	
	public JerseyConfig() {
		
		packages("org.glassfish.jersey.examples.multipart");
		register(MultiPartFeature.class);
		
		register(ImageEndpoint.class);
	}
}
