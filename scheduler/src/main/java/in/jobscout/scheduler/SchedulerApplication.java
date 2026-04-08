package in.jobscout.scheduler;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

// Reminder: keep scheduling enabled so DailyTrigger runs automatically.
@EnableScheduling
@SpringBootApplication(scanBasePackages = {"in.jobscout.scheduler", "com.jobscout.scheduler"})
public class SchedulerApplication {

	public static void main(String[] args) {
		SpringApplication.run(SchedulerApplication.class, args);
	}

}
