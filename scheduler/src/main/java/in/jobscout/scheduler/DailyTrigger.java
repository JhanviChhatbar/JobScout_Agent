package in.jobscout.scheduler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;

@Component
@Slf4j
public class DailyTrigger {

    @Value("${jobscout.agent.script-path:../agent/main.py}")
    private String scriptPath;

    @Value("${jobscout.agent.python-path:python}")
    private String pythonPath;

    /**
     * Scheduled daily trigger at 3:30 AM UTC.
     * Runs the Job Scout Agent Python script.
     */
    @Scheduled(cron = "0 30 3 * * *")
    public void triggerAgentRun() {
        String timestamp = LocalDateTime.now()
            .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        log.info("Starting daily job scout run at {}", timestamp);
        executeAgent();
    }

    /**
     * Manual trigger for testing (can be called via REST endpoint or directly).
     */
    public void triggerManually() {
        log.info("Starting manual job scout trigger");
        executeAgent();
    }

    /**
     * Execute the Python agent script.
     */
    private void executeAgent() {
        ProcessBuilder pb = new ProcessBuilder(pythonPath, scriptPath);
        pb.directory(new File(scriptPath).getParentFile());
        pb.redirectErrorStream(true);

        Process process = null;
        try {
            process = pb.start();
            log.info("Agent process started");

            // Read output line by line
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    log.info("Agent: {}", line);
                }
            }

            // Wait for process completion with 10-minute timeout
            boolean finished = process.waitFor(10, TimeUnit.MINUTES);
            if (finished) {
                int exitCode = process.exitValue();
                log.info("Agent process completed with exit code: {}", exitCode);
            } else {
                log.warn("Agent process timed out after 10 minutes");
                process.destroyForcibly();
            }

        } catch (Exception e) {
            log.error("Failed to execute job scout agent", e);
        } finally {
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
            }
        }
    }
}

