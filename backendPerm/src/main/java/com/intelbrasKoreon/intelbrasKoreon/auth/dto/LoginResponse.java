package com.intelbrasKoreon.intelbrasKoreon.auth.dto;

public record LoginResponse(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn,
        UserInfo user
) {
    public record UserInfo(Long id, String name, String email, String role, Long tenantId) {}
}
