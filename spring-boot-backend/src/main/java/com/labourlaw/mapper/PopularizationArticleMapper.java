package com.labourlaw.mapper;

import com.labourlaw.entity.PopularizationArticle;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface PopularizationArticleMapper {

    @Select("SELECT * FROM popularization_articles ORDER BY id")
    List<PopularizationArticle> findAll();

    @Select("SELECT * FROM popularization_articles WHERE id = #{id}")
    PopularizationArticle findById(Long id);

    @Update("UPDATE popularization_articles SET content=#{content}, sources=#{sources}, generated_at=NOW() WHERE id=#{id}")
    int updateGenerated(@Param("id") Long id,
                        @Param("content") String content,
                        @Param("sources") String sources);
}
