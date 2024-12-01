from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import mysql.connector
import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'sua-chave-secreta'  # Troque por uma chave segura
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Função para conectar ao banco de dados
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="master",
        database="school"
    )

# Rota para obter todos os alunos
@app.route('/alunos', methods=['GET'])
def get_alunos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Retorna resultados como dicionários
        cursor.execute(
            "SELECT A.id_aluno, A.nome, A.genero, A.serie, A.matricula, U.status FROM Aluno A JOIN Usuario U ON A.fk_Usuario_id_usuario = U.id_usuario")
        resultados = cursor.fetchall()
        return jsonify(resultados), 200  # Retorna os dados como JSON
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

def criar_nome_usuario(nome, nomeTabela):
    try:
        nomes = nome.split()
        primeiro_nome = nomes[0].lower()
        ultimo_nome = nomes[-1].lower() if len(nomes) > 1 else ''
        nome_usuario = f"{primeiro_nome}_{ultimo_nome}"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verifica se o nome de usuário já existe
        cursor.execute("SELECT COUNT(*) as numero_usuarios FROM Usuario WHERE nome_usuario = %s", (nome_usuario,))
        count = cursor.fetchone()['numero_usuarios']

        if count > 0:
            cursor.execute("SELECT COUNT(*) AS total FROM " + nomeTabela)
            contador = cursor.fetchone()['total'] + 1
            nome_usuario = f"{nome_usuario}{contador}"

        return nome_usuario
    except IndexError:
        return "Nome inválido. Forneça pelo menos um nome."
    finally:
        cursor.close()
        conn.close()

def gerar_codigo(prefixo, nomeTabela):
    try:
        ano_corrente = datetime.datetime.now().year % 100  # Pega os dois últimos dígitos do ano
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Retorna resultados como dicionários
        cursor.execute("SELECT COUNT(*) AS total FROM " + nomeTabela)
        resultados = cursor.fetchall()
        contador = int(resultados[0]['total']) + 1
        return f"{prefixo}{ano_corrente:02d}{contador:04d}"
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para adicionar um novo aluno
@app.route('/alunos', methods=['POST'])
def add_aluno():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Retorna resultados como dicionários

        data = request.json  # Obtém dados do corpo da requisição
        nome = data.get('nome')
        data_nascimento = data.get('data_nascimento')
        genero = data.get('genero')
        cpf = data.get('cpf')
        serie = data.get('serie')
        endereco = data.get('endereco')
        nome_responsavel = data.get('nome_responsavel')
        telefone_responsavel = data.get('telefone_responsavel')

        # Verifica se já existe um aluno com o mesmo CPF
        cursor.execute("SELECT * FROM Aluno WHERE cpf = %s", (cpf,))
        aluno_existente_cpf = cursor.fetchone()

        if aluno_existente_cpf:
            return jsonify({"error": "Já existe um aluno cadastrado com esse CPF."}), 400

        # Gera a matrícula e verifica se já existe um aluno com a mesma matrícula
        matricula = gerar_codigo("EST", "Aluno")

        # Define nome de usuário e senha como a matrícula
        nome_usuario = criar_nome_usuario(nome, "Aluno")
        senha = matricula
        senha_codificada = bcrypt.generate_password_hash(senha).decode('utf-8')

        # Insere o usuário na tabela Usuario
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Usuario (nome_usuario, senha, tipo_usuario, status) VALUES (%s, %s, %s, %s)", 
                    (nome_usuario, senha_codificada, "Aluno", "Ativo"))

        # Obtém o ID do usuário recém-inserido
        id_usuario = cursor.lastrowid

        # Insere o aluno na tabela Aluno
        cursor.execute("INSERT INTO Aluno (nome, data_nascimento, genero, cpf, serie, matricula, endereco, nome_responsavel, telefone_responsavel, fk_Usuario_id_usuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (nome, data_nascimento, genero, cpf, serie, matricula, endereco, nome_responsavel, telefone_responsavel, id_usuario))
        
        conn.commit()  # Confirma a transação
        return jsonify({"message": "Aluno adicionado com sucesso!", "Matricula": matricula}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para buscar um aluno pela matricula
@app.route('/alunos/<int:id_aluno>', methods=['GET'])
def get_aluno_by_matricula(id_aluno):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Aluno WHERE id_aluno = %s", (id_aluno,))
        resultado = cursor.fetchone()
        if resultado:
            return jsonify(resultado), 200
        else:
            return jsonify({"message": "Aluno não encontrado"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para atualizar um aluno
@app.route('/alunos/<int:id_aluno>', methods=['PUT'])
def update_aluno(id_aluno):
    try:
        data = request.json
        nome = data.get('nome')
        data_nascimento = data.get('data_nascimento')
        genero = data.get('genero')
        cpf = data.get('cpf')
        endereco = data.get('endereco')
        nome_responsavel = data.get('nome_responsavel')
        telefone_responsavel = data.get('telefone_responsavel')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Aluno WHERE id_aluno = %s", (id_aluno,))
        resultado = cursor.fetchone()
        if resultado:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Aluno SET nome = %s, data_nascimento = %s, genero = %s, cpf = %s, endereco = %s, nome_responsavel = %s, telefone_responsavel = %s WHERE id_aluno = %s", (nome, data_nascimento, genero, cpf, endereco, nome_responsavel, telefone_responsavel, id_aluno))
            conn.commit()
            return jsonify({"message": "Aluno atualizado com sucesso!"}), 200
        else:
            return jsonify({"message": "Aluno não encontrado"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para deletar um aluno
@app.route('/alunos/<int:id_aluno>', methods=['DELETE'])
def delete_aluno(id_aluno):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT fk_Usuario_id_usuario AS id_usuario FROM Aluno WHERE id_aluno = %s", (id_aluno,))
        
        usuario = cursor.fetchone()  # Armazena o resultado
        if usuario:
            id_usuario = int(usuario['id_usuario'])
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Aluno WHERE id_aluno = %s", (id_aluno,))
            cursor.execute("DELETE FROM Usuario WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            return jsonify({"message": "Aluno deletado com sucesso!"}), 200
        else:
            return jsonify({"message": "Aluno não encontrado"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()





# Rota para adicionar um professor
@app.route('/professores', methods=['POST'])
def add_professor():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Retorna resultados como dicionários

        data = request.json  # Obtém dados do corpo da requisição
        nome = data.get('nome')
        genero = data.get('genero')
        cpf = data.get('cpf')
        email = data.get('email')
        telefone = data.get('telefone')
        especialidade = data.get('especialidade')
        endereco = data.get('endereco')

        # Verifica se já existe um aluno com o mesmo CPF
        cursor.execute("SELECT * FROM Professor WHERE cpf = %s", (cpf,))
        professor_existente_cpf = cursor.fetchone()

        if professor_existente_cpf:
            return jsonify({"error": "Já existe um professor cadastrado com esse CPF."}), 400

        # Gera a matrícula e verifica se já existe um aluno com a mesma matrícula
        codigo = gerar_codigo("PROF", "Professor")

        # Define nome de usuário e senha como a matrícula
        nome_usuario = criar_nome_usuario(nome, "Professor")
        senha = codigo
        senha_codificada = bcrypt.generate_password_hash(senha).decode('utf-8')

        # Insere o usuário na tabela Usuario
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Usuario (nome_usuario, senha, tipo_usuario, status) VALUES (%s, %s, %s, %s)", 
                    (nome_usuario, senha_codificada, "Professor", "Ativo"))

        # Obtém o ID do usuário recém-inserido
        id_usuario = cursor.lastrowid

        # Insere o aluno na tabela Aluno
        cursor.execute("INSERT INTO Professor (nome, genero, cpf, codigo, email, telefone, especialidade, endereco, status, fk_Usuario_id_usuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (nome, genero, cpf, codigo, email, telefone, especialidade, endereco, "Ativo", id_usuario))
        
        conn.commit()  # Confirma a transação
        return jsonify({"message": "Professor adicionado com sucesso!", "Código": codigo}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para listar todos os professores
@app.route('/professores', methods=['GET'])
def get_professores():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Professor")
        professores = cursor.fetchall()
        return jsonify(professores), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para buscar um professor por CODIGO
@app.route('/professores/<int:id_professor>', methods=['GET'])
def get_professor(id_professor):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Professor WHERE codigo = %s", (id_professor,))
        professor = cursor.fetchone()
        if professor:
            return jsonify(professor), 200
        else:
            return jsonify({"message": "Professor não encontrado"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para atualizar informações de um professor
@app.route('/professores/<int:id_professor>', methods=['PUT'])
def update_professor(id_professor):
    try:
        data = request.json
        nome = data.get('nome')
        genero = data.get('genero')
        cpf = data.get('cpf')
        email = data.get('email')
        telefone = data.get('telefone')
        especialidade = data.get('especialidade')
        endereco = data.get('endereco')
        status = data.get('status')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Professor WHERE id_professor = %s", (id_professor,))
        professor = cursor.fetchone()
        if professor:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE Professor 
                SET nome = %s, genero = %s, cpf = %s, email = %s, telefone = %s, especialidade = %s, endereco = %s, status = %s
                WHERE id_professor = %s
                """,
                (nome, genero, cpf, email, telefone, especialidade, endereco, status, id_professor)
            )
            conn.commit()
            return jsonify({"message": "Professor atualizado com sucesso!"}), 200
        else:
            return jsonify({"message": "Professor não encontrado"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rota para remover um professor (DELETE)
@app.route('/professores/<int:id_professor>', methods=['DELETE'])
def delete_professor(id_professor):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT fk_Usuario_id_usuario AS id_usuario FROM Professor WHERE id_professor = %s", (id_professor,))
        usuario = cursor.fetchone()

        if usuario:
            id_usuario = int(usuario['id_usuario'])
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Professor WHERE codigo = %s", (id_professor,))
            cursor.execute("DELETE FROM Usuario WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            return jsonify({"message": "Professor deletado com sucesso!"}), 200
        else:
            return jsonify({"message": "Professor não encontrado!"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()






# Rota para cadastrar disciplinas
@app.route('/disciplinas', methods=['POST'])
def cadastrar_disciplina():
    try:
        data = request.get_json()
        nome = data['nome']
        codigo = data['codigo']
        descricao = data['descricao']
        carga_horaria = data['carga']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Disciplina (nome_disciplina, codigo, descricao, carga_horaria) VALUES (%s, %s, %s, %s)", (nome, codigo, descricao, carga_horaria))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Disciplina cadastrada com sucesso!'}), 201
    except mysql.connector.errors.IntegrityError:
            return jsonify({'error': 'Já existe uma disciplina com este código'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para listar disciplinas
@app.route('/disciplinas', methods=['GET'])
def listar_disciplinas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Disciplina")
        disciplinas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(disciplinas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Rota para listar disciplina po ID
@app.route('/disciplinas/<int:id_disciplina>', methods=['GET'])
def get_disciplina(id_disciplina):
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Disciplina WHERE id_disciplina = %s", (id_disciplina,))
        disciplinas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(disciplinas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para atualizar uma disciplina
@app.route('/disciplinas/<int:id_disciplina>', methods=['PUT'])
def atualizar_disciplina(id_disciplina):
    try:
        data = request.get_json()
        nome = data.get('nome')
        codigo = data.get('codigo')
        descricao = data.get('descricao')
        carga_horaria = data.get('carga')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Disciplina
            SET nome_disciplina = %s, codigo = %s, descricao = %s, carga_horaria = %s
            WHERE id_disciplina = %s
            """,
            (nome, codigo, descricao, carga_horaria, id_disciplina)
        )
        if cur.rowcount == 0:
            return jsonify({'error': 'Disciplina não encontrada'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Disciplina atualizada com sucesso!'}), 200
    except mysql.connector.errors.IntegrityError:
            return jsonify({'error': 'Já existe uma disciplina com este código'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para deletar uma disciplina
@app.route('/disciplinas/<int:id_disciplina>', methods=['DELETE'])
def deletar_disciplina(id_disciplina):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Disciplina WHERE id_disciplina = %s", (id_disciplina,))
        if cur.rowcount == 0:
            return jsonify({'error': 'Disciplina não encontrada'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Disciplina deletada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500








# Rota para inserir uma turma
@app.route('/turmas', methods=['POST'])
def inserir_turma():
    try:
        data = request.get_json()
        nome = data['nome']
        capacidade = data['capacidade']
        serie = data['serie']
        ano_letivo = data['ano_letivo']
        semestre = data['semestre']
        fk_professor = data['fk_professor']
        fk_disciplina = data['fk_disciplina']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Turma (nome, capacidade, serie, ano_letivo, semestre, fk_Professor_id_professor, fk_Disciplina_id_disciplina)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (nome, capacidade, serie, ano_letivo, semestre, fk_professor, fk_disciplina)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Turma cadastrada com sucesso!'}), 201
    except mysql.connector.errors.IntegrityError:
        return jsonify({'error': 'Já existe uma turma com este nome'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para listar todas as turmas
@app.route('/turmas', methods=['GET'])
def listar_turmas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Turma")
        turmas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(turmas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para listar uma turma por ID
@app.route('/turmas/<int:id_turma>', methods=['GET'])
def listar_turma_por_id(id_turma):
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Turma WHERE id_turma = %s", (id_turma,))
        turma = cur.fetchone()
        cur.close()
        conn.close()
        if turma:
            return jsonify(turma), 200
        else:
            return jsonify({'error': 'Turma não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para atualizar uma turma
@app.route('/turmas/<int:id_turma>', methods=['PUT'])
def atualizar_turma(id_turma):
    try:
        data = request.get_json()
        nome = data.get('nome')
        capacidade = data.get('capacidade')
        serie = data.get('serie')
        ano_letivo = data.get('ano_letivo')
        semestre = data.get('semestre')
        fk_professor = data.get('fk_professor')
        fk_disciplina = data.get('fk_disciplina')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Turma
            SET nome = %s, capacidade = %s, serie = %s, ano_letivo = %s, semestre = %s,
                fk_Professor_id_professor = %s, fk_Disciplina_id_disciplina = %s
            WHERE id_turma = %s
            """,
            (nome, capacidade, serie, ano_letivo, semestre, fk_professor, fk_disciplina, id_turma)
        )
        if cur.rowcount == 0:
            return jsonify({'error': 'Turma não encontrada'}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Turma atualizada com sucesso!'}), 200
    except mysql.connector.errors.IntegrityError:
        return jsonify({'error': 'Já existe uma turma com este nome'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para deletar uma turma
@app.route('/turmas/<int:id_turma>', methods=['DELETE'])
def deletar_turma(id_turma):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Turma WHERE id_turma = %s", (id_turma,))
        if cur.rowcount == 0:
            return jsonify({'error': 'Turma não encontrada'}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Turma deletada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500










# Rotas para tabela Aula
@app.route('/aulas', methods=['POST'])
def inserir_aula():
    try:
        data = request.get_json()
        data_aula = data['data_aula']
        hora_inicio = data['hora_inicio']
        hora_fim = data['hora_fim']
        dados = data['dados']
        fk_turma = data['fk_turma']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Aula (data_aula, hora_inicio, hora_fim, dados, fk_Turma_id_turma)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (data_aula, hora_inicio, hora_fim, dados, fk_turma)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Aula cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/aulas', methods=['GET'])
def listar_aulas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Aula")
        aulas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(aulas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/aula/<int:id_aula>', methods=['GET'])
def listar_aula_por_id(id_aula):
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Aula WHERE id_aula = %s", (id_aula,))
        aula = cur.fetchone()
        cur.close()
        conn.close()
        if aula:
            return jsonify(aula), 200
        else:
            return jsonify({'error': 'Aula não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/aulas/<int:id_aula>', methods=['PUT'])
def atualizar_aula(id_aula):
    try:
        data = request.get_json()
        data_aula = data.get('data_aula')
        hora_inicio = data.get('hora_inicio')
        hora_fim = data.get('hora_fim')
        dados = data.get('dados')
        fk_turma = data.get('fk_turma')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Aula
            SET data_aula = %s, hora_inicio = %s, hora_fim = %s, dados = %s, fk_Turma_id_turma = %s
            WHERE id_aula = %s
            """,
            (data_aula, hora_inicio, hora_fim, dados, fk_turma, id_aula)
        )
        if cur.rowcount == 0:
            return jsonify({'error': 'Aula não encontrada'}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Aula atualizada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/aulas/<int:id_aula>', methods=['DELETE'])
def deletar_aula(id_aula):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Aula WHERE id_aula = %s", (id_aula,))
        if cur.rowcount == 0:
            return jsonify({'error': 'Aula não encontrada'}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Aula deletada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    





# Rotas para tabela Presenca
@app.route('/presencas', methods=['POST'])
def inserir_presenca():
    try:
        data = request.get_json()
        status = data['status']
        hora_chegada = data['hora_chegada']
        fk_aluno = data['fk_aluno']
        fk_aula = data['fk_aula']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Presenca (status, hora_chegada, fk_Aluno_id_aluno, fk_Aula_id_aula)
            VALUES (%s, %s, %s, %s)
            """,
            (status, hora_chegada, fk_aluno, fk_aula)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Presença cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/presencas', methods=['GET'])
def listar_presencas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Presenca")
        presencas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(presencas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/presencas/<int:id_presenca>', methods=['GET'])
def listar_presenca_por_id(id_presenca):
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Presenca WHERE id_presenca = %s", (id_presenca,))
        presenca = cur.fetchone()
        cur.close()
        conn.close()
        if presenca:
            return jsonify(presenca), 200
        else:
            return jsonify({'error': 'Presença não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/presencas/<int:id_presenca>', methods=['PUT'])
def atualizar_presenca(id_presenca):
    try:
        data = request.get_json()
        status = data.get('status')
        hora_chegada = data.get('hora_chegada')
        fk_aluno = data.get('fk_aluno')
        fk_aula = data.get('fk_aula')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Presenca
            SET status = %s, hora_chegada = %s, fk_Aluno_id_aluno = %s, fk_Aula_id_aula = %s
            WHERE id_presenca = %s
            """,
            (status, hora_chegada, fk_aluno, fk_aula, id_presenca)
        )
        if cur.rowcount == 0:
            return jsonify({'error': 'Presença não encontrada'}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Presença atualizada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/presenca/<int:id_presenca>', methods=['DELETE'])
def deletar_presenca(id_presenca):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Presenca WHERE id_presenca = %s", (id_presenca,))
        if cur.rowcount == 0:
            return jsonify({'error': 'Presença não encontrada'}), 404

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Presença deletada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500










@app.route('/ocorrencias', methods=['POST'])
def cadastrar_ocorrencia():
    try:
        data = request.get_json()
        descricao = data['descricao']
        tipo = data['tipo']
        fk_Professor_id_professor = data['fk_Professor_id_professor']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Ocorrencia (descricao, tipo, fk_Professor_id_professor)
            VALUES (%s, %s, %s)
        """, (descricao, tipo, fk_Professor_id_professor))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Ocorrência cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/ocorrencias', methods=['GET'])
def listar_ocorrencias():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Ocorrencia")
        ocorrencias = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(ocorrencias), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/ocorrencia/<int:id_ocorrencia>', methods=['GET'])
def obter_ocorrencia(id_ocorrencia):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Ocorrencia WHERE id_ocorrencia = %s", (id_ocorrencia,))
        ocorrencia = cur.fetchone()
        cur.close()
        conn.close()
        
        if ocorrencia:
            return jsonify(ocorrencia), 200
        else:
            return jsonify({'error': 'Ocorrência não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/ocorrencias/<int:id_ocorrencia>', methods=['PUT'])
def atualizar_ocorrencia(id_ocorrencia):
    try:
        data = request.get_json()
        descricao = data.get('descricao')
        tipo = data.get('tipo')
        fk_Professor_id_professor = data.get('fk_Professor_id_professor')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Ocorrencia
            SET descricao = %s, tipo = %s, fk_Professor_id_professor = %s
            WHERE id_ocorrencia = %s
        """, (descricao, tipo, fk_Professor_id_professor, id_ocorrencia))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Ocorrência atualizada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/ocorrencias/<int:id_ocorrencia>', methods=['DELETE'])
def excluir_ocorrencia(id_ocorrencia):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Ocorrencia WHERE id_ocorrencia = %s", (id_ocorrencia,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Ocorrência excluída com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    





@app.route('/historico', methods=['POST'])
def cadastrar_historico_ocorrencia():
    try:
        data = request.get_json()
        fk_Aluno_id_aluno = data['fk_Aluno_id_aluno']
        fk_Ocorrencia_id_ocorrencia = data['fk_Ocorrencia_id_ocorrencia']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Historico_Ocorrencia (fk_Aluno_id_aluno, fk_Ocorrencia_id_ocorrencia)
            VALUES (%s, %s)
        """, (fk_Aluno_id_aluno, fk_Ocorrencia_id_ocorrencia))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Histórico de Ocorrência cadastrado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/historico/<int:id_historico_ocorrencia>', methods=['DELETE'])
def excluir_historico_ocorrencia(id_historico_ocorrencia):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Historico_Ocorrencia WHERE id_historico_ocorrencia = %s", (id_historico_ocorrencia,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Histórico de Ocorrência excluído com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historico/<int:id_historico_ocorrencia>', methods=['PUT'])
def atualizar_historico_ocorrencia(id_historico_ocorrencia):
    try:
        data = request.get_json()
        fk_Aluno_id_aluno = data.get('fk_Aluno_id_aluno')
        fk_Ocorrencia_id_ocorrencia = data.get('fk_Ocorrencia_id_ocorrencia')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Historico_Ocorrencia
            SET fk_Aluno_id_aluno = %s, fk_Ocorrencia_id_ocorrencia = %s
            WHERE id_historico_ocorrencia = %s
        """, (fk_Aluno_id_aluno, fk_Ocorrencia_id_ocorrencia, id_historico_ocorrencia))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Histórico de Ocorrência atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

@app.route('/historico', methods=['GET'])
def listar_historicos_ocorrencia():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Historico_Ocorrencia")
        historicos = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(historicos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historico/<int:id_historico_ocorrencia>', methods=['GET'])
def obter_historico_ocorrencia(id_historico_ocorrencia):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Historico_Ocorrencia WHERE id_historico_ocorrencia = %s", (id_historico_ocorrencia,))
        historico = cur.fetchone()
        cur.close()
        conn.close()
        
        if historico:
            return jsonify(historico), 200
        else:
            return jsonify({'error': 'Histórico de Ocorrência não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500






# Inserção de Administrador
@app.route('/administradores', methods=['POST']) 
def cadastrar_administrador():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Retorna resultados como dicionários

        data = request.json  # Obtém dados do corpo da requisição
        nome = data['nome']
        cargo = data['cargo']
        email = data['email']

        # Define nome de usuário e senha como a matrícula
        nome_usuario = criar_nome_usuario(nome, "Administrador")
        senha = "1234"
        senha_codificada = bcrypt.generate_password_hash(senha).decode('utf-8')

        # Insere o usuário na tabela Usuario
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Usuario (nome_usuario, senha, tipo_usuario, status) VALUES (%s, %s, %s, %s)", 
                    (nome_usuario, senha_codificada, "Administrador", "Ativo"))

        id_usuario = cursor.lastrowid

        cursor.execute("""
            INSERT INTO Administrador (nome, cargo, email, fk_Usuario_id_usuario)
            VALUES (%s, %s, %s, %s)
        """, (nome, cargo, email, id_usuario))
        
        conn.commit()
        return jsonify({"message": "Administrador adicionado com sucesso!"}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Exclusão de Administrador
@app.route('/administradores/<int:id_administrador>', methods=['DELETE'])
def excluir_administrador(id_administrador):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT fk_Usuario_id_usuario AS id_usuario FROM Administrador WHERE id_administrador = %s", (id_administrador,))
        usuario = cursor.fetchone()

        if usuario:
            id_usuario = int(usuario['id_usuario'])
            cur = conn.cursor()
            cur.execute("DELETE FROM Administrador WHERE id_administrador = %s", (id_administrador,))
            cursor.execute("DELETE FROM Usuario WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'mensagem': 'Administrador excluído com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Atualização de Administrador
@app.route('/administradores/<int:id_administrador>', methods=['PUT'])
def atualizar_administrador(id_administrador):
    try:
        data = request.get_json()
        nome = data.get('nome')
        cargo = data.get('cargo')
        email = data.get('email')
        fk_Usuario_id_usuario = data.get('fk_Usuario_id_usuario')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Administrador
            SET nome = %s, cargo = %s, email = %s, fk_Usuario_id_usuario = %s
            WHERE id_administrador = %s
        """, (nome, cargo, email, fk_Usuario_id_usuario, id_administrador))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Administrador atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Seleção Total de Administradores
@app.route('/administradores', methods=['GET'])
def listar_administradores():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Administrador")
        administradores = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(administradores), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Seleção de Administrador por ID
@app.route('/administradores/<int:id_administrador>', methods=['GET'])
def obter_administrador(id_administrador):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Administrador WHERE id_administrador = %s", (id_administrador,))
        administrador = cur.fetchone()
        cur.close()
        conn.close()
        if administrador:
            return jsonify(administrador), 200
        return jsonify({'mensagem': 'Administrador não encontrado!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
# Inserção de Nota
@app.route('/notas', methods=['POST'])
def cadastrar_nota():
    try:
        data = request.get_json()
        nota = data['nota']
        fk_Turma_id_turma = data['fk_Turma_id_turma']
        fk_Aluno_id_aluno = data['fk_Aluno_id_aluno']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Nota (nota, fk_Turma_id_turma, fk_Aluno_id_aluno)
            VALUES (%s, %s, %s)
        """, (nota, fk_Turma_id_turma, fk_Aluno_id_aluno))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Nota cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Exclusão de Nota
@app.route('/notas/<int:id_nota>', methods=['DELETE'])
def excluir_nota(id_nota):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Nota WHERE id_nota = %s", (id_nota,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Nota excluída com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Atualização de Nota
@app.route('/notas/<int:id_nota>', methods=['PUT'])
def atualizar_nota(id_nota):
    try:
        data = request.get_json()
        nota = data.get('nota')
        fk_Turma_id_turma = data.get('fk_Turma_id_turma')
        fk_Aluno_id_aluno = data.get('fk_Aluno_id_aluno')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Nota
            SET nota = %s, fk_Turma_id_turma = %s, fk_Aluno_id_aluno = %s
            WHERE id_nota = %s
        """, (nota, fk_Turma_id_turma, fk_Aluno_id_aluno, id_nota))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Nota atualizada com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Seleção Total de Notas
@app.route('/notas', methods=['GET'])
def listar_notas():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Nota")
        notas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(notas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Seleção de Nota por ID
@app.route('/notas/<int:id_nota>', methods=['GET'])
def obter_nota(id_nota):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Nota WHERE id_nota = %s", (id_nota,))
        nota = cur.fetchone()
        cur.close()
        conn.close()
        if nota:
            return jsonify(nota), 200
        return jsonify({'mensagem': 'Nota não encontrada!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500




# Inserção de Usuário
@app.route('/usuarios', methods=['POST'])
def cadastrar_usuario():
    try:
        data = request.get_json()
        nome_usuario = data['nome_usuario']
        senha = data['senha']
        tipo_usuario = data['tipo_usuario']
        status = data['status']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Usuario (nome_usuario, senha, tipo_usuario, status)
            VALUES (%s, %s, %s, %s)
        """, (nome_usuario, senha, tipo_usuario, status))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Usuário cadastrado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Exclusão de Usuário
@app.route('/usuarios/<int:id_usuario>', methods=['DELETE'])
def excluir_usuario(id_usuario):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Usuario WHERE id_usuario = %s", (id_usuario,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Usuário excluído com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Atualização de Usuário
@app.route('/usuarios/<int:id_usuario>', methods=['PUT'])
def atualizar_usuario(id_usuario):
    try:
        data = request.get_json()
        nome_usuario = data.get('nome_usuario')
        senha = data.get('senha')
        tipo_usuario = data.get('tipo_usuario')
        status = data.get('status')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Usuario
            SET nome_usuario = %s, senha = %s, tipo_usuario = %s, status = %s
            WHERE id_usuario = %s
        """, (nome_usuario, senha, tipo_usuario, status, id_usuario))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Usuário atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Seleção Total de Usuários
@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Usuario")
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Seleção de Usuário por ID
@app.route('/usuarios/<int:id_usuario>', methods=['GET'])
def obter_usuario(id_usuario):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Usuario WHERE id_usuario = %s", (id_usuario,))
        usuario = cur.fetchone()
        cur.close()
        conn.close()
        if usuario:
            return jsonify(usuario), 200
        return jsonify({'mensagem': 'Usuário não encontrado!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500











# Rota para cadastrar aluno em uma turma
@app.route('/cadastrar_aluno_turma', methods=['POST'])
def cadastrar_aluno_turma():
    try:
        data = request.get_json()
        id_aluno = data['matricula']
        id_turma = data['id_turma']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Nota (nota, fk_Aluno_id_aluno, fk_Turma_id_turma) VALUES (%s, %s, %s)", (0, id_aluno, id_turma))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'mensagem': 'Aluno cadastrado na turma com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para cadastrar a nota do aluno em uma turma
@app.route('/cadastrar_nota', methods=['PUT'])
def cadastrar_notaN():
    try:
        data = request.get_json()
        nota = data['nota']
        id_turma = data['id_turma']
        id_aluno = data['id_aluno']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Nota SET nota = %s WHERE fk_Aluno_id_aluno = %s AND fk_Turma_id_turma = %s", (nota, id_aluno, id_turma))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'mensagem': 'Nota cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para registrar a presença de um aluno em uma aula
@app.route('/registrar_presenca', methods=['POST'])
def registrar_presenca():
    try:
        data = request.get_json()
        status = data['status']
        hora_chegada = data['hora_chegada']
        id_aluno = data['id_aluno']
        id_aula = data['id_aula']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Presenca (status, hora_chegada, fk_Aluno_id_aluno, fk_Aula_id_aula) VALUES (%s, %s, %s, %s)", (status, hora_chegada, id_aluno, id_aula))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'mensagem': 'Presença registrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para registrar uma ocorrência para um aluno
@app.route('/registrar_ocorrencia', methods=['POST'])
def registrar_ocorrencia():
    try:
        data = request.get_json()
        descricao = data['descricao']
        tipo = data['tipo']
        id_professor = data['id_professor']
        id_aluno = data['id_aluno']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO Ocorrencia (descricao, tipo, fk_Professor_id_professor) VALUES (%s, %s, %s)", (descricao, tipo, id_professor))
        id_ocorrencia = cursor.lastrowid
        
        cursor.execute("INSERT INTO Historico_Ocorrencia (fk_Aluno_id_aluno, fk_Ocorrencia_id_ocorrencia) VALUES (%s, %s)", (id_aluno, id_ocorrencia))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'mensagem': 'Ocorrência registrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para mostrar todas as turmas com o nome da respectiva disciplina em que um aluno está matriculado
@app.route('/turmas_aluno/<int:id_aluno>', methods=['GET'])
def turmas_aluno(id_aluno):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT D.nome_disciplina, T.nome AS nome_turma, P.nome
            FROM Turma AS T
            INNER JOIN Disciplina AS D ON T.fk_Disciplina_id_disciplina = D.id_disciplina
            INNER JOIN Nota AS AT ON T.id_turma = AT.fk_Turma_id_turma
            INNER JOIN Professor AS P ON T.fk_Professor_id_professor = P.id_professor
            WHERE AT.fk_Aluno_id_aluno = %s
        """, (id_aluno,))
        
        turmas = []
        for row in cursor.fetchall():
            turmas.append({'nome_turma': row[1], 'nome_disciplina': row[0], 'professor': row[2]})
        
        cursor.close()
        conn.close()
        
        return jsonify(turmas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Rota para cadastrar turmas
@app.route('/cadastrar_turma', methods=['POST'])
def cadastrar_turma():
    try:
        data = request.get_json()
        nome = data['nome']
        capacidade = data['capacidade']
        serie = data['serie']
        ano_letivo = data['ano_letivo']
        semestre = data['semestre']
        id_professor = data['id_professor']
        id_disciplina = data['id_disciplina']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Turma (nome, capacidade, serie, ano_letivo, semestre, fk_Professor_id_professor, fk_Disciplina_id_disciplina) VALUES (%s, %s, %s, %s, %s, %s, %s)", (nome, capacidade, serie, ano_letivo, semestre, id_professor, id_disciplina))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Turma cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para cadastrar aulas
@app.route('/cadastrar_aula', methods=['POST'])
def cadastrar_aula():
    try:
        data = request.get_json()
        data_aula = data['data_aula']
        hora_inicio = data['hora_inicio']
        hora_fim = data['hora_fim']
        dados = data['dados']
        id_turma = data['id_turma']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Aula (data_aula, hora_inicio, hora_fim, dados, fk_Turma_id_turma) VALUES (%s, %s, %s, %s, %s)", (data_aula, hora_inicio, hora_fim, dados, id_turma))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Aula cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


















# Rota para registrar novos usuários
@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        username = data['username']
        password = data['password']
        tipo_usuario = data['user']

        # Hash da senha
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Usuario (nome_usuario, senha, tipo_usuario, status) VALUES (%s, %s, %s, %s)", (username, password_hash, tipo_usuario, "Ativo")
        )
        conn.commit()
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Para para login
@app.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        usuario = data['usuario']
        senha = data['senha']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuario WHERE nome_usuario = %s", (usuario,))
        user = cursor.fetchone()

        id_usuario = None
        if user and bcrypt.check_password_hash(user['senha'], senha):
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Aluno INNER JOIN Usuario ON Aluno.fk_Usuario_id_usuario = Usuario.id_usuario WHERE Usuario.id_usuario = %s", (user['id_usuario'], )) 
            id_usuario = cursor.fetchone()
            
            if id_usuario:
                # Criação do token JWT
                access_token = create_access_token(identity={"id": id_usuario['id_aluno'], "type": user['tipo_usuario']})
                return jsonify({"access_token": access_token}), 200
            else:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM Professor INNER JOIN Usuario ON Professor.fk_Usuario_id_usuario = Usuario.id_usuario WHERE Usuario.id_usuario = %s", (user['id_usuario'], )) 
                id_usuario = cursor.fetchone()

                if id_usuario:
                    # Criação do token JWT
                    access_token = create_access_token(identity={"id": id_usuario['id_professor'], "type": user['tipo_usuario']})
                    return jsonify({"access_token": access_token}), 200
                else:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM Administrador INNER JOIN Usuario ON Administrador.fk_Usuario_id_usuario = Usuario.id_usuario WHERE Usuario.id_usuario = %s", (user['id_usuario'], )) 
                    id_usuario = cursor.fetchone()

                    if id_usuario:
                        # Criação do token JWT
                        access_token = create_access_token(identity={"id": id_usuario['id_administrador'], "type": user['tipo_usuario']})
                        return jsonify({"access_token": access_token}), 200

        else:
            return jsonify({"error": "Usuário ou senha inválidos"}), 401
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Rpta de proteção (exemplo)
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    return jsonify({"message": "Acesso permitido! Você está autenticado."}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
