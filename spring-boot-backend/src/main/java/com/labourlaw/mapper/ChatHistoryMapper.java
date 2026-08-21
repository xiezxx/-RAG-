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

    /** 全部用户的问答记录（管理员视角，含用户名），created_at 用 DATE_FORMAT 转为字符串避免时区/序列化问题 */
    @Select("SELECT ch.id, ch.question, ch.answer, ch.sources, ch.rating, ch.feedback, " +
            "DATE_FORMAT(ch.created_at, '%Y-%m-%d %H:%i:%s') AS createdAt, u.username, ch.user_id AS userId " +
            "FROM chat_history ch JOIN users u ON ch.user_id = u.id " +
            "ORDER BY ch.created_at DESC LIMIT #{limit}")
    List<Map<String, Object>> findAllWithUserJoin(@Param("limit") int limit);

    /** 所有普通用户（role='USER'）的问答记录：普通用户可见范围 = 自己 + 其他普通用户，不含管理员 */
    @Select("SELECT ch.id, ch.question, ch.answer, ch.sources, ch.rating, ch.feedback, " +
            "DATE_FORMAT(ch.created_at, '%Y-%m-%d %H:%i:%s') AS createdAt, u.username, ch.user_id AS userId " +
            "FROM chat_history ch JOIN users u ON ch.user_id = u.id " +
            "WHERE u.role = 'USER' " +
            "ORDER BY ch.created_at DESC LIMIT #{limit}")
    List<Map<String, Object>> findByUserRole(@Param("limit") int limit);

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
