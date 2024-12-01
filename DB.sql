/* Lógico_29.11: */

CREATE DATABASE school;
USE school;

CREATE TABLE Aluno (
    id_aluno int PRIMARY KEY AUTO_INCREMENT,
    nome varchar(255),
    data_nascimento date,
    genero enum('Masculino', 'Femenino'),
    cpf varchar(14) UNIQUE,
    serie enum('Primeira', 'Segunda', 'Terceira'),
    matricula varchar(50) UNIQUE,
    endereco varchar(255),
    nome_responsavel varchar(255),
    telefone_responsavel varchar(20),
    fk_Usuario_id_usuario int UNIQUE
);

CREATE TABLE Professor (
    id_professor int PRIMARY KEY AUTO_INCREMENT,
    nome varchar(255),
    genero enum('Masculino', 'Femenino'),
    cpf varchar(14) UNIQUE,
    codigo varchar(50) UNIQUE,
    email varchar(255),
    telefone varchar(20),
    especialidade varchar(255),
    endereco varchar(255),
    status enum('Ativo', 'Inativo'),
    fk_Usuario_id_usuario int UNIQUE
);

CREATE TABLE Disciplina (
    id_disciplina int PRIMARY KEY AUTO_INCREMENT,
    nome_disciplina varchar(255),
    codigo varchar(50) UNIQUE,
    descricao text,
    carga_horaria int
);

CREATE TABLE Aula (
    id_aula int PRIMARY KEY AUTO_INCREMENT,
    data_aula date,
    hora_inicio time,
    hora_fim time,
    dados text,
    fk_Turma_id_turma int
);

CREATE TABLE Presenca (
    id_presenca int PRIMARY KEY AUTO_INCREMENT,
    status enum('Presente', 'Ausente'),
    hora_chegada time,
    fk_Aluno_id_aluno int,
    fk_Aula_id_aula int
);

CREATE TABLE Ocorrencia (
    id_ocorrencia int PRIMARY KEY AUTO_INCREMENT,
    descricao text,
    tipo varchar(50),
    fk_Professor_id_professor int
);

CREATE TABLE Historico_Ocorrencia (
    id_historico_ocorrencia int PRIMARY KEY AUTO_INCREMENT,
    data_ocorrencia datetime default now(),
    fk_Aluno_id_aluno int,
    fk_Ocorrencia_id_ocorrencia int UNIQUE
);

CREATE TABLE Usuario (
    id_usuario int PRIMARY KEY AUTO_INCREMENT,
    nome_usuario varchar(255) UNIQUE,
    senha varchar(255),
    tipo_usuario enum('Aluno', 'Professor', 'Administrador'),
    data_criacao datetime default now(),
    status enum('Ativo', 'Inativo')
);

CREATE TABLE Administrador (
    id_administrador int PRIMARY KEY AUTO_INCREMENT,
    nome varchar(255),
    cargo varchar(50),
    email varchar(255),
    fk_Usuario_id_usuario int UNIQUE
);

CREATE TABLE Turma (
    id_turma int PRIMARY KEY AUTO_INCREMENT,
    nome varchar(50) UNIQUE,
    capacidade int,
    serie enum('Primeira', 'Segunda', 'Terceira'),
    ano_letivo year,
    semestre enum('Primeiro', 'Segundo'),
    fk_Professor_id_professor int,
    fk_Disciplina_id_disciplina int
);

CREATE TABLE Nota (
    id_nota int PRIMARY KEY AUTO_INCREMENT,
    nota decimal(3, 1),
    fk_Turma_id_turma int,
    fk_Aluno_id_aluno int
);
 
ALTER TABLE Aluno ADD CONSTRAINT FK_Aluno_1
    FOREIGN KEY (fk_Usuario_id_usuario)
    REFERENCES Usuario (id_usuario)
    ON DELETE RESTRICT;
 
ALTER TABLE Professor ADD CONSTRAINT FK_Professor_1
    FOREIGN KEY (fk_Usuario_id_usuario)
    REFERENCES Usuario (id_usuario)
    ON DELETE RESTRICT;
    
ALTER TABLE Administrador ADD CONSTRAINT FK_Administrador_1
    FOREIGN KEY (fk_Usuario_id_usuario)
    REFERENCES Usuario (id_usuario)
	ON DELETE RESTRICT;
 
ALTER TABLE Aula ADD CONSTRAINT FK_Aula_1
    FOREIGN KEY (fk_Turma_id_turma)
    REFERENCES Turma (id_turma)
    ON DELETE CASCADE;
 
ALTER TABLE Presenca ADD CONSTRAINT FK_Presenca_1
    FOREIGN KEY (fk_Aluno_id_aluno)
    REFERENCES Aluno (id_aluno)
    ON DELETE RESTRICT;

ALTER TABLE Presenca ADD CONSTRAINT FK_Presenca_2
    FOREIGN KEY (fk_Aula_id_aula)
    REFERENCES Aula (id_aula)
    ON DELETE RESTRICT;
 
ALTER TABLE Ocorrencia ADD CONSTRAINT FK_Ocorrencia_1
    FOREIGN KEY (fk_Professor_id_professor)
    REFERENCES Professor (id_professor)
    ON DELETE RESTRICT;
 
ALTER TABLE Historico_Ocorrencia ADD CONSTRAINT FK_Historico_Ocorrencia_1
    FOREIGN KEY (fk_Aluno_id_aluno)
    REFERENCES Aluno (id_aluno)
	ON DELETE RESTRICT;
 
ALTER TABLE Historico_Ocorrencia ADD CONSTRAINT FK_Historico_Ocorrencia_2
    FOREIGN KEY (fk_Ocorrencia_id_ocorrencia)
    REFERENCES Ocorrencia (id_ocorrencia)
    ON DELETE CASCADE;
 
ALTER TABLE Turma ADD CONSTRAINT FK_Turma_1
    FOREIGN KEY (fk_Professor_id_professor)
    REFERENCES Professor (id_professor)
    ON DELETE SET NULL;
    
ALTER TABLE Turma ADD CONSTRAINT FK_Turma_2
    FOREIGN KEY (fk_Disciplina_id_disciplina)
    REFERENCES Disciplina (id_disciplina)
    ON DELETE CASCADE;
 
ALTER TABLE Nota ADD CONSTRAINT FK_Nota_1
    FOREIGN KEY (fk_Aluno_id_aluno)
    REFERENCES Aluno (id_aluno)
    ON DELETE CASCADE;
    
ALTER TABLE Nota ADD CONSTRAINT FK_Nota_2
    FOREIGN KEY (fk_Turma_id_turma)
    REFERENCES Turma (id_turma)
    ON DELETE CASCADE;


--------------------------------------------------------------------------------------
SELECT 
    Aluno.matricula, 
    Aluno.nome, 
    Aluno.serie, 
    AVG(Nota.nota) AS media, 
    COUNT(Aula.id_aula) AS total_aula, 
    COUNT(CASE WHEN Presenca.status = 'Presente' THEN Presenca.id_presenca END) AS total_presenca,
    COUNT(Aula.id_aula) - COUNT(CASE WHEN Presenca.status = 'Presente' THEN Presenca.id_presenca END) AS total_falta,
    JSON_ARRAYAGG(Ocorrencia.descricao) AS ocorrencias, 
    JSON_ARRAYAGG(Turma.nome) AS turmas
FROM Aluno
LEFT JOIN Nota ON Aluno.id_aluno = Nota.fk_Aluno_id_aluno
LEFT JOIN Presenca ON Aluno.id_aluno = Presenca.fk_Aluno_id_aluno
LEFT JOIN Aula ON Presenca.fk_Aula_id_aula = Aula.id_aula
LEFT JOIN Historico_Ocorrencia ON Aluno.id_aluno = Historico_Ocorrencia.fk_Aluno_id_aluno
LEFT JOIN Ocorrencia ON Historico_Ocorrencia.fk_Ocorrencia_id_ocorrencia = Ocorrencia.id_ocorrencia
LEFT JOIN Turma ON Nota.fk_Turma_id_turma = Turma.id_turma
GROUP BY Aluno.id_aluno;    