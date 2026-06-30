package com.intelbrasKoreon.intelbrasKoreon.user;

import com.intelbrasKoreon.intelbrasKoreon.auth.dto.LoginResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','TENANT_ADMIN')")
    public List<LoginResponse.UserInfo> listByTenant(@AuthenticationPrincipal User caller) {
        Long tenantId = caller.getRole() == UserRole.SUPER_ADMIN
                ? null
                : caller.getTenantId();
        List<User> users = tenantId != null
                ? userService.findByTenant(tenantId)
                : userService.findByTenant(caller.getTenantId());
        return users.stream().map(this::toInfo).toList();
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','TENANT_ADMIN')")
    public ResponseEntity<LoginResponse.UserInfo> create(
            @RequestBody Map<String, String> body,
            @AuthenticationPrincipal User caller
    ) {
        Long tenantId = body.containsKey("tenantId")
                ? Long.parseLong(body.get("tenantId"))
                : caller.getTenantId();
        UserRole role = UserRole.valueOf(body.getOrDefault("role", "OPERATOR"));
        User created = userService.create(tenantId, body.get("name"), body.get("email"), body.get("password"), role);
        return ResponseEntity.ok(toInfo(created));
    }

    @PatchMapping("/{id}/role")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','TENANT_ADMIN')")
    public ResponseEntity<LoginResponse.UserInfo> changeRole(
            @PathVariable Long id,
            @RequestBody Map<String, String> body
    ) {
        User updated = userService.changeRole(id, UserRole.valueOf(body.get("role")));
        return ResponseEntity.ok(toInfo(updated));
    }

    @PatchMapping("/{id}/deactivate")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','TENANT_ADMIN')")
    public ResponseEntity<LoginResponse.UserInfo> deactivate(@PathVariable Long id) {
        return ResponseEntity.ok(toInfo(userService.setActive(id, false)));
    }

    @PatchMapping("/{id}/password")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','TENANT_ADMIN')")
    public ResponseEntity<Void> resetPassword(@PathVariable Long id, @RequestBody Map<String, String> body) {
        userService.resetPassword(id, body.get("password"));
        return ResponseEntity.noContent().build();
    }

    private LoginResponse.UserInfo toInfo(User u) {
        return new LoginResponse.UserInfo(u.getId(), u.getName(), u.getEmail(), u.getRole().name(), u.getTenantId());
    }
}
