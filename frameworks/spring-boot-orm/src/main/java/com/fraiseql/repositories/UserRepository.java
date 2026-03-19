package com.fraiseql.repositories;

import com.fraiseql.entities.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Repository
public interface UserRepository extends JpaRepository<User, Integer> {

    @Query(value = "SELECT * FROM benchmark.tb_user WHERE id = CAST(:id AS uuid)", nativeQuery = true)
    User findByUuid(@Param("id") String id);

    @Query(value = "SELECT * FROM benchmark.tb_user ORDER BY created_at DESC LIMIT :limit", nativeQuery = true)
    List<User> findUsersWithLimit(@Param("limit") int limit);

    @Modifying
    @Transactional
    @Query(value = "UPDATE benchmark.tb_user SET bio = :bio, updated_at = NOW() WHERE id = CAST(:id AS uuid)", nativeQuery = true)
    int updateBioByUuid(@Param("id") String id, @Param("bio") String bio);
}