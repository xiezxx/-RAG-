-- 迁移脚本：将 labour_cases 表的 facts 列改为 case_content
-- 在 MySQL 中执行此脚本

ALTER TABLE labour_cases ADD COLUMN case_content TEXT AFTER judge_date;
UPDATE labour_cases SET case_content = facts;
ALTER TABLE labour_cases DROP COLUMN facts;
