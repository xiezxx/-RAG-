package com.labourlaw.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Statute {
    private Long id;
    private String name;
    private String category;
    private Integer articleCount;
    private String documentNumber;       // 文号
    private String issuingAuthority;     // 发布机关
    private String publishDate;          // 发布日期
    private String effectiveDate;        // 生效日期
    private String expiryDate;           // 失效日期
    private String status;               // 现行有效/已被修订/已废止
    private String applicableRegion;     // 适用地区
    private String applicableSubject;    // 适用主体
    private LocalDateTime createdAt;
}
