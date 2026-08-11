package com.labourlaw.mapper;

import com.labourlaw.entity.*;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface StatuteMapper {
    @Select("SELECT * FROM statutes ORDER BY category, name")
    List<Statute> findAll();

    @Select("SELECT * FROM statutes WHERE category = #{category} ORDER BY name")
    List<Statute> findByCategory(String category);

    @Select("SELECT * FROM statutes WHERE id = #{id}")
    Statute findById(Long id);

    @Insert("INSERT INTO statutes (name, category, article_count, publish_date, effective_date, status, document_number, issuing_authority, applicable_region, applicable_subject, created_at) " +
            "VALUES (#{name}, #{category}, #{articleCount}, #{publishDate}, #{effectiveDate}, #{status}, #{documentNumber}, #{issuingAuthority}, #{applicableRegion}, #{applicableSubject}, NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Statute statute);

    @Update("UPDATE statutes SET name=#{name}, category=#{category}, article_count=#{articleCount}, " +
            "publish_date=#{publishDate}, effective_date=#{effectiveDate}, status=#{status}, " +
            "document_number=#{documentNumber}, issuing_authority=#{issuingAuthority}, " +
            "applicable_region=#{applicableRegion}, applicable_subject=#{applicableSubject} WHERE id=#{id}")
    int update(Statute statute);

    @Delete("DELETE FROM statutes WHERE id = #{id}")
    int deleteById(Long id);

    @Select("SELECT COUNT(*) FROM statutes")
    int count();
}
