package com.intelbrasKoreon.intelbrasKoreon.auth;

import com.intelbrasKoreon.intelbrasKoreon.user.User;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Service
public class JwtService {

    @Value("${app.jwt.secret}")
    private String secret;

    @Value("${app.jwt.expiration-ms}")
    private long expirationMs;

    @Value("${app.jwt.refresh-expiration-ms}")
    private long refreshExpirationMs;

    private SecretKey getKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    public String generateToken(User user) {
        return buildToken(user, expirationMs, false);
    }

    public String generateRefreshToken(User user) {
        return buildToken(user, refreshExpirationMs, true);
    }

    private String buildToken(User user, long ttlMs, boolean isRefresh) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("tenant_id", user.getTenantId());
        claims.put("role", user.getRole().name());
        claims.put("name", user.getName());
        if (isRefresh) claims.put("refresh", true);

        return Jwts.builder()
                .claims(claims)
                .subject(user.getEmail())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + ttlMs))
                .signWith(getKey())
                .compact();
    }

    public String extractEmail(String token) {
        return parseClaims(token).getSubject();
    }

    public Long extractTenantId(String token) {
        Object raw = parseClaims(token).get("tenant_id");
        if (raw == null) return null;
        return ((Number) raw).longValue();
    }

    public boolean isTokenValid(String token, String expectedEmail) {
        try {
            String email = extractEmail(token);
            return email.equals(expectedEmail) && !isExpired(token);
        } catch (JwtException e) {
            return false;
        }
    }

    private boolean isExpired(String token) {
        return parseClaims(token).getExpiration().before(new Date());
    }

    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(getKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
