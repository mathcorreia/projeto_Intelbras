package com.intelbrasKoreon.intelbrasKoreon.websocket;

import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class EventBrokerService {

    private final SimpMessagingTemplate messagingTemplate;

    public void publishEvent(Long tenantId, String type, Object payload) {
        messagingTemplate.convertAndSend(
                "/topic/tenant/" + tenantId + "/events",
                new BrokerMessage(type, payload)
        );
    }

    public void publishAlarm(Long tenantId, Object payload) {
        messagingTemplate.convertAndSend(
                "/topic/tenant/" + tenantId + "/alarms",
                new BrokerMessage("alarm", payload)
        );
    }

    public void publishGuaritaAlert(Long tenantId, Object payload) {
        messagingTemplate.convertAndSend(
                "/topic/tenant/" + tenantId + "/guarita",
                new BrokerMessage("guarita_alert", payload)
        );
    }

    public record BrokerMessage(String type, Object payload) {}
}
