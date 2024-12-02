-- Inserts na tabela Aluno
INSERT INTO Aluno (nome, data_nascimento, genero, cpf, serie, matricula, endereco, nome_responsavel, telefone_responsavel, status, fk_Usuario_id_usuario) VALUES
('João Silva', '2005-04-15', 'Masculino', '123.456.789-00', 'Primeira', 'EST001', 'Rua A, 123', 'Maria Silva', '(47) 91234-5678', 'Ativo', 1),
('Ana Souza', '2006-08-20', 'Femenino', '987.654.321-00', 'Segunda', 'EST002', 'Rua B, 456', 'Carlos Souza', '(47) 92345-6789', 'Ativo', 4),
('Pedro Costa', '2005-02-10', 'Masculino', '321.654.987-00', 'Terceira', 'EST003', 'Rua C, 789', 'Fernanda Costa', '(47) 93456-7890', 'Inativo', NULL),
('Mariana Lopes', '2007-06-25', 'Femenino', '654.321.987-00', 'Primeira', 'EST004', 'Rua D, 101', 'Paulo Lopes', '(47) 94567-8901', 'Ativo', NULL),
('Carlos Santos', '2006-12-01', 'Masculino', '789.123.456-00', 'Segunda', 'EST005', 'Rua E, 202', 'Luciana Santos', '(47) 95678-9012', 'Inativo', NULL);