package com.labourlaw.mapper;

import com.labourlaw.entity.DiagnosisReport;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface DiagnosisReportMapper {

    @Insert("INSERT INTO diagnosis_reports " +
            "(user_id, reason, years, monthly_wage, has_contract, description, " +
            " summary, issues, warnings, next_steps, estimation, sources) " +
            "VALUES (#{userId}, #{reason}, #{years}, #{monthlyWage}, #{hasContract}, #{description}, " +
            " #{summary}, #{issues}, #{warnings}, #{nextSteps}, #{estimation}, #{sources})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DiagnosisReport report);

    /** 当前用户的历史报告列表（description 截断 80 字，不含详情 JSON） */
    @Select("SELECT id, user_id, reason, years, monthly_wage, has_contract, " +
            "LEFT(description, 80) AS description, summary, estimation, " +
            "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at " +
            "FROM diagnosis_reports WHERE user_id = #{userId} ORDER BY id DESC LIMIT 50")
    List<DiagnosisReport> findByUser(@Param("userId") Long userId);

    @Select("SELECT id, user_id, reason, years, monthly_wage, has_contract, description, " +
            "summary, issues, warnings, next_steps, estimation, sources, " +
            "DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at " +
            "FROM diagnosis_reports WHERE id = #{id}")
    DiagnosisReport findById(@Param("id") Long id);
}
