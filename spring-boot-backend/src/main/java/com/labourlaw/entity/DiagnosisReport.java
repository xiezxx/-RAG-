package com.labourlaw.entity;

import lombok.Data;

/**
 * 案情诊断报告（诊断成功后落库，供历史查看与下载）
 */
@Data
public class DiagnosisReport {
    private Long id;
    private Long userId;
    private String reason;          // 纠纷类型
    private Double years;           // 工龄
    private Double monthlyWage;     // 月工资
    private Integer hasContract;    // 是否签订合同 1/0
    private String description;     // 案情描述（列表接口为截断后的 80 字）
    private String summary;         // 诊断结论
    private String issues;          // JSON 字符串 [问题清单]
    private String warnings;        // JSON 字符串 [风险提示]
    private String nextSteps;       // JSON 字符串 [行动建议]
    private String estimation;      // JSON 字符串 {N,N_plus_1,2N,months,note}
    private String sources;         // JSON 字符串 [来源]
    // 注意：本项目 TIMESTAMP 列无法映射到 LocalDateTime（既有全局问题），用 String 接收
    private String createdAt;
}
