package com.intelbrasKoreon.intelbrasKoreon.auth;

import com.intelbrasKoreon.intelbrasKoreon.auth.dto.LoginRequest;
import com.intelbrasKoreon.intelbrasKoreon.auth.dto.LoginResponse;
import com.intelbrasKoreon.intelbrasKoreon.user.User;
import com.intelbrasKoreon.intelbrasKoreon.user.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final JwtService jwtService;
    private final PasswordEncoder passwordEncoder;

    @Value("${app.jwt.expiration-ms}")
    private long expirationMs;

    public LoginResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.email())
                .orElseThrow(() -> new BadCredentialsException("Credenciais inválidas"));

        if (!user.isActive()) {
            throw new BadCredentialsException("Usuário inativo");
        }

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new BadCredentialsException("Credenciais inválidas");
        }

        String accessToken = jwtService.generateToken(user);
        String refreshToken = jwtService.generateRefreshToken(user);

        return new LoginResponse(
                accessToken,
                refreshToken,
                "Bearer",
                expirationMs / 1000,
                new LoginResponse.UserInfo(
                        user.getId(),
                        user.getName(),
                        user.getEmail(),
                        user.getRole().name(),
                        user.getTenantId()
                )
        );
    }

    public LoginResponse refresh(String refreshToken) {
        String email = jwtService.extractEmail(refreshToken);
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new BadCredentialsException("Token inválido"));

        if (!jwtService.isTokenValid(refreshToken, email)) {
            throw new BadCredentialsException("Refresh token inválido ou expirado");
        }

        String newAccessToken = jwtService.generateToken(user);
        String newRefreshToken = jwtService.generateRefreshToken(user);

        return new LoginResponse(
                newAccessToken,
                newRefreshToken,
                "Bearer",
                expirationMs / 1000,
                new LoginResponse.UserInfo(
                        user.getId(), user.getName(), user.getEmail(),
                        user.getRole().name(), user.getTenantId()
                )
        );
    }
}
