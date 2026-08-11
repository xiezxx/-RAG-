package com.labourlaw.mapper;

import com.labourlaw.entity.*;
import org.apache.ibatis.annotations.*;
import java.util.List;
import java.util.Map;

@Mapper
public interface ChatHistoryMapper {
    @Insert("INSERT INTO chat_history (user_id, question, answer, sources, created_at) " +
            "VALUES (#{userId}, #{question}, #{answer}, #{sources}, NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ChatHistory history);

    @Select("SELECT * FROM chat_history WHERE user_id = #{userId} ORDER BY created_at DESC LIMIT #{limit}")
    List<ChatHistory> findByUserId(@Param("userId") Long userId, @Param("limit") int limit);

    @Select("SELECT * FROM chat_history WHERE id = #{id}")
    ChatHistory findById(Long id);

    @Update("UPDATE chat_history SET rating=#{rating}, feedback=#{feedback} WHERE id=#{id} AND user_id=#{userId}")
    int updateRating(@Param("id") Long id, @Param("userId") Long userId,
                     @Param("rating") int rating, @Param("feedback") String feedback);

    @Select("SELECT ch.id, ch.question, ch.answer, ch.sources, ch.rating, ch.feedback, ch.created_at AS createdAt, u.username " +
            "FROM chat_history ch JOIN users u ON ch.user_id = u.id " +
            "ORDER BY ch.created_at DESC LIMIT #{limit}")
    List<Map<String, Object>> findAllWithUserJoin(@Param("limit") int limit);

    @Select("SELECT COUNT(*) FROM chat_history")
    int count();

    @Select("SELECT AVG(rating) FROM chat_history WHERE rating > 0")
    Double avgRating();

    @Select("SELECT rating, COUNT(*) AS cnt FROM chat_history WHERE rating > 0 GROUP BY rating ORDER BY rating")
    List<Map<String, Object>> ratingDistribution();

    @Select("SELECT COUNT(*) FROM labour_cases")
    int countCases();

    @Select("SELECT COUNT(DISTINCT court) FROM labour_cases")
    int countDistinctCourts();
}
