from PIL import Image
import os

def comprimir_imagem(caminho_imagem, caminho_saida, max_width=800, max_height=800, qualidade=70):
    """
    Comprime e redimensiona uma imagem para economizar espaço.
    
    :param caminho_imagem: Caminho da imagem original
    :param caminho_saida: Caminho onde a imagem comprimida será salva
    :param max_width: Largura máxima da imagem
    :param max_height: Altura máxima da imagem
    :param qualidade: Qualidade da imagem comprimida (0 a 100)
    """
    if not os.path.exists(caminho_imagem):
        print(f"O arquivo {caminho_imagem} não foi encontrado.")
        return

    try:
        with Image.open(caminho_imagem) as img:
            print(f"Abrindo a imagem: {img.format} {img.size}")
            # Redimensiona a imagem
            img.thumbnail((max_width, max_height))

            # Verifica se a imagem é JPEG para aplicar qualidade
            if img.format == 'JPEG':  # Corrigido para 'JPEG'
                img.save(caminho_saida, optimize=True, quality=qualidade)
            else:
                img.save(caminho_saida, optimize=True)

            print(f"Imagem salva em {caminho_saida}")

    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")

def comprimir_pasta(caminho_pasta_origem, caminho_pasta_saida, max_width=800, max_height=800, qualidade=70):
    """
    Comprime todas as imagens em uma pasta.
    
    :param caminho_pasta_origem: Caminho da pasta com as imagens originais
    :param caminho_pasta_saida: Caminho da pasta onde as imagens comprimidas serão salvas
    :param max_width: Largura máxima das imagens
    :param max_height: Altura máxima das imagens
    :param qualidade: Qualidade das imagens comprimidas (0 a 100)
    """
    if not os.path.exists(caminho_pasta_saida):
        os.makedirs(caminho_pasta_saida)

    for arquivo in os.listdir(caminho_pasta_origem):
        caminho_imagem = os.path.join(caminho_pasta_origem, arquivo)
        if os.path.isfile(caminho_imagem) and arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
            caminho_saida = os.path.join(caminho_pasta_saida, arquivo)
            comprimir_imagem(caminho_imagem, caminho_saida, max_width, max_height, qualidade)

# Exemplo de uso
caminho_pasta_origem = "imagem"  # Pasta com as imagens originais
caminho_pasta_saida = "imagens_comprimidas"  # Pasta para salvar as imagens comprimidas
comprimir_pasta(caminho_pasta_origem, caminho_pasta_saida)
