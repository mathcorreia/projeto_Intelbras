package com.intelbrasKoreon.intelbrasKoreon.websocket;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Endpoint HTTP interno usado pelo Python FastAPI para publicar eventos
 * no broker WebSocket sem depender de JWT.
 * Protegido por API key configurável (BROKER_API_KEY env var).
 */
@RestController
@RequestMapping("/broker")
@RequiredArgsConstructor
public class EventBrokerController {

    private final EventBrokerService brokerService;

    @Value("${app.broker.api-key}")
    private String expectedApiKey;

    @PostMapping("/event")
    public ResponseEntity<Void> receiveEvent(
            @RequestHeader("X-Broker-Key") String apiKey,
            @RequestBody Map<String, Object> body
    ) {
        if (!expectedApiKey.equals(apiKey)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        Long tenantId = ((Number) body.getOrDefault("tenant_id", 1)).longValue();
        String type = (String) body.getOrDefault("type", "event");
        Object payload = body.get("payload");

        switch (type) {
            case "alarm"          -> brokerService.publishAlarm(tenantId, payload);
            case "guarita_alert"  -> brokerService.publishGuaritaAlert(tenantId, payload);
            default               -> brokerService.publishEvent(tenantId, type, payload);
        }

        return ResponseEntity.ok().build();
    }
}
