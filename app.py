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
        cursor = conn.cursor()
        cursor.execute("UPDATE Aluno SET nome = %s, data_nascimento = %s, genero = %s, cpf = %s, endereco = %s, nome_responsavel = %s, telefone_responsavel = %s WHERE id_aluno = %s", (nome, data_nascimento, genero, cpf, endereco, nome_responsavel, telefone_responsavel, id_aluno))
        conn.commit()
        if cursor.rowcount > 0:
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

# Rota para cadastrar aluno em uma turma
@app.route('/cadastrar_aluno_turma', methods=['POST'])
def cadastrar_aluno_turma():
    try:
        data = request.get_json()
        matricula = data['matricula']
        id_turma = data['id_turma']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Nota (nota, fk_Aluno_id_aluno, fk_Turma_id_turma) VALUES (%s, %s, %s)", (0, matricula, id_turma))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'mensagem': 'Aluno cadastrado na turma com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para cadastrar a nota do aluno em uma turma
@app.route('/cadastrar_nota', methods=['PUT'])
def cadastrar_nota():
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

# Rota para cadastrar disciplinas
@app.route('/cadastrar_disciplina', methods=['POST'])
def cadastrar_disciplina():
    try:
        data = request.get_json()
        nome_disciplina = data['nome_disciplina']
        codigo = data['codigo']
        descricao = data['descricao']
        carga_horaria = data['carga_horaria']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Disciplina (nome_disciplina, codigo, descricao, carga_horaria) VALUES (%s, %s, %s, %s)", (nome_disciplina, codigo, descricao, carga_horaria))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Disciplina cadastrada com sucesso!'}), 201
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
        conteudo = data['conteudo']
        id_turma = data['id_turma']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Aula (data_aula, hora_inicio, hora_fim, conteudo, fk_Turma_id_turma) VALUES (%s, %s, %s, %s, %s)", (data_aula, hora_inicio, hora_fim, conteudo, id_turma))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'mensagem': 'Aula cadastrada com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

















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

# 2. Rota para listar todos os professores
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

        if cursor.rowcount > 0:
            return jsonify({"message": "Professor atualizado com sucesso!"}), 200
        else:
            return jsonify({"message": "Professor não encontrado"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# 5. Rota para remover um professor (DELETE)
@app.route('/professores/<int:id_professor>', methods=['DELETE'])
def delete_professor(id_professor):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT fk_Usuario_id_usuario AS id_usuario FROM Professor WHERE codigo = %s", (id_professor,))
        
        usuario = cursor.fetchone()  # Armazena o resultado
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
