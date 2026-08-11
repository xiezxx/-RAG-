package com.labourlaw.config;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Set;

/**
 * JWT 认证过滤器 —— 拦截所有 /api/** 请求，校验 Authorization Bearer Token。
 * 放行 /api/auth/**（登录/注册无需认证）。
 */
@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    /** 无需认证的白名单路径 */
    private static final Set<String> WHITELIST = Set.of(
            "/api/auth/login",
            "/api/auth/register"
    );

    /** OPTIONS 预检请求放行 */
    private static final Set<String> ALLOWED_METHODS = Set.of("OPTIONS");

    private final JwtUtil jwtUtil;

    public JwtAuthFilter(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String path = request.getRequestURI();
        String method = request.getMethod();

        // 放行白名单
        if (WHITELIST.contains(path)) {
            filterChain.doFilter(request, response);
            return;
        }

        // 放行 OPTIONS 预检
        if (ALLOWED_METHODS.contains(method)) {
            filterChain.doFilter(request, response);
            return;
        }

        // 只拦截 /api/ 开头的请求
        if (!path.startsWith("/api/")) {
            filterChain.doFilter(request, response);
            return;
        }

        // 提取 Authorization Header
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            sendUnauthorized(response, "未提供有效的认证令牌");
            return;
        }

        String token = authHeader.substring(7);
        if (!jwtUtil.validateToken(token)) {
            sendUnauthorized(response, "认证令牌无效或已过期");
            return;
        }

        // 将用户信息注入 request attribute，方便 Controller 使用
        request.setAttribute("userId", jwtUtil.getUserId(token));
        request.setAttribute("username", jwtUtil.getUsername(token));
        request.setAttribute("role", jwtUtil.getRole(token));

        filterChain.doFilter(request, response);
    }

    private void sendUnauthorized(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"" + message + "\"}");
    }
}
