package in.jobscout.scheduler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;

@Component
@Slf4j
public class DailyTrigger {

    @Scheduled(cron = "0 30 3 * * *") // 9 AM IST = 03:30 UTC
    public void triggerAgentRun() {
        runAgentProcess();
    }

    public void triggerManually() {
        runAgentProcess();
    }

    private void runAgentProcess() {
        log.info("Starting daily job scout run...");

        try {
            ProcessBuilder processBuilder = new ProcessBuilder("python", "main.py");
            processBuilder.directory(new File("../agent"));

            Process process = processBuilder.start();

            CompletableFuture<String> stdoutFuture = CompletableFuture.supplyAsync(
                    () -> readStream(process.getInputStream())
            );
            CompletableFuture<String> stderrFuture = CompletableFuture.supplyAsync(
                    () -> readStream(process.getErrorStream())
            );

            int exitCode = process.waitFor();
            String stdout = stdoutFuture.join();
            String stderr = stderrFuture.join();

            if (!stdout.isBlank()) {
                log.info("Daily job scout stdout:\n{}", stdout);
            }
            if (!stderr.isBlank()) {
                log.error("Daily job scout stderr:\n{}", stderr);
            }

            log.info("Daily job scout process exited with code: {}", exitCode);
        } catch (Exception ex) {
            log.error("Error while running daily job scout process", ex);
        }
    }

    private String readStream(InputStream stream) {
        try (InputStream in = stream) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException ex) {
            return "Failed to read process stream: " + ex.getMessage();
        }
    }
}

