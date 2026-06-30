package com.intelbrasKoreon.intelbrasKoreon.auth;

import com.intelbrasKoreon.intelbrasKoreon.auth.dto.LoginRequest;
import com.intelbrasKoreon.intelbrasKoreon.auth.dto.LoginResponse;
import com.intelbrasKoreon.intelbrasKoreon.user.User;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @PostMapping("/refresh")
    public ResponseEntity<LoginResponse> refresh(@RequestBody Map<String, String> body) {
        String token = body.get("refreshToken");
        if (token == null || token.isBlank()) {
            return ResponseEntity.badRequest().build();
        }
        return ResponseEntity.ok(authService.refresh(token));
    }

    @GetMapping("/me")
    public ResponseEntity<LoginResponse.UserInfo> me(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(new LoginResponse.UserInfo(
                user.getId(), user.getName(), user.getEmail(),
                user.getRole().name(), user.getTenantId()
        ));
    }
}
