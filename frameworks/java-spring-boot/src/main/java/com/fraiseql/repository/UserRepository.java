package com.fraiseql.repository;

import com.fraiseql.models.User;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Integer> {
    List<User> findAllByOrderByUsername(Pageable pageable);

    @Query("SELECT u FROM User u WHERE u.id = :uuid")
    Optional<User> findByUuid(@Param("uuid") String uuid);
}
