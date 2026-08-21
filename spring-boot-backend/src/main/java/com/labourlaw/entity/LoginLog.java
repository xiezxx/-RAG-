package com.labourlaw.entity;

import lombok.Data;

/** 登录记录（每次登录尝试：成功/失败 + IP） */
@Data
public class LoginLog {
    private Long id;
    private Long userId;
    private String username;
    private String ip;
    private Boolean success;
    private String message;
    private String createdAt;
}
