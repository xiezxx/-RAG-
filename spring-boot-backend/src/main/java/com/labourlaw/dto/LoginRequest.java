package com.labourlaw.dto;

import lombok.Data;

@Data
public class LoginRequest {
    private String username;
    private String password;
    private String name;     // 姓名（注册用）
    private String phone;    // 手机号（注册用）
}
