package in.jobscout.scheduler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

/**
 * REST API controller for manual trigger and health check endpoints.
 */
@RestController
@RequestMapping("/api")
@Slf4j
public class ManualTriggerController {

    private final DailyTrigger dailyTrigger;

    public ManualTriggerController(DailyTrigger dailyTrigger) {
        this.dailyTrigger = dailyTrigger;
    }

    /**
     * POST /api/trigger
     * Triggers a manual job scout run in a background thread.
     * Returns 202 Accepted immediately without waiting for completion.
     */
    @PostMapping("/trigger")
    public ResponseEntity<Map<String, Object>> triggerAgent() {
        log.info("Manual trigger requested via REST API");

        // Run in a new thread to avoid blocking the HTTP response
        new Thread(dailyTrigger::triggerManually).start();

        Map<String, Object> response = new HashMap<>();
        response.put("message", "Job scout run triggered");
        response.put("timestamp", LocalDateTime.now()
            .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));

        return ResponseEntity.status(HttpStatus.ACCEPTED).body(response);
    }

    /**
     * GET /api/health
     * Health check endpoint.
     * Returns 200 OK with service status.
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "ok");
        response.put("service", "job-scout-scheduler");

        return ResponseEntity.ok(response);
    }
}
