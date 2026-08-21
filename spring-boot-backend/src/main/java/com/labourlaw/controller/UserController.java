package com.labourlaw.controller;

import com.labourlaw.dto.*;
import com.labourlaw.entity.LoginLog;
import com.labourlaw.entity.User;
import com.labourlaw.mapper.LoginLogMapper;
import com.labourlaw.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import javax.servlet.http.HttpServletRequest;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private LoginLogMapper loginLogMapper;

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody LoginRequest request, HttpServletRequest httpRequest) {
        try {
            LoginResponse resp = userService.login(request);
            // 记录成功登录（尽力而为，不影响登录结果）
            try {
                LoginLog log = new LoginLog();
                log.setUsername(request.getUsername());
                log.setIp(httpRequest.getRemoteAddr());
                log.setSuccess(true);
                log.setMessage("登录成功");
                loginLogMapper.insert(log);
            } catch (Exception ignored) {}
            return Map.of("code", 200, "data", resp, "message", "登录成功");
        } catch (Exception e) {
            // 记录失败登录（尽力而为）
            try {
                LoginLog log = new LoginLog();
                log.setUsername(request.getUsername());
                log.setIp(httpRequest.getRemoteAddr());
                log.setSuccess(false);
                log.setMessage(e.getMessage());
                loginLogMapper.insert(log);
            } catch (Exception ignored) {}
            return Map.of("code", 401, "message", e.getMessage());
        }
    }

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody LoginRequest request) {
        try {
            User user = userService.register(request);
            user.setPassword(null);
            return Map.of("code", 200, "data", user, "message", "注册成功");
        } catch (Exception e) {
            return Map.of("code", 400, "message", e.getMessage());
        }
    }
}
