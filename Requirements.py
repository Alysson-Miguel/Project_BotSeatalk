import os
import re
from pathlib import Path

def get_all_imports():
    """Extrai todos os imports de arquivos .py"""
    imports = set()
    
    for py_file in Path('.').glob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Padrão para capturar imports
                patterns = [
                    r'^\s*import\s+([^\s]+)',
                    r'^\s*from\s+([^\s]+)\s+import'
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    for match in matches:
                        root = match.split('.')[0]
                        imports.add(root)
        except:
            pass
    
    return imports

# Bibliotecas padrão do Python (não precisam no requirements)
STDLIB = {
    'os', 'sys', 'json', 're', 'time', 'datetime', 'logging',
    'collections', 'functools', 'typing', 'pathlib', 'io',
    'threading', 'asyncio', 'http', 'urllib', 'traceback'
}

all_imports = get_all_imports()
external = sorted(all_imports - STDLIB)

print("🔥 DEPENDÊNCIAS EXTERNAS ENCONTRADAS:")
print("=" * 40)
for dep in external:
    print(f"  • {dep}")

print("\n📋 VERIFICANDO requirements.txt:")
print("=" * 40)

try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read().lower()
        
    missing = []
    found = []
    
    for dep in external:
        if dep.lower() in requirements:
            found.append(dep)
            print(f"  ✅ {dep}")
        else:
            missing.append(dep)
            print(f"  ❌ {dep} - FALTANDO!")
    
    if missing:
        print(f"\n⚠️  ATENÇÃO: {len(missing)} dependência(s) faltando!")
        print("\nAdicione no requirements.txt:")
        for dep in missing:
            print(f"  {dep}")
    else:
        print(f"\n✅ Todas as {len(found)} dependências estão no requirements.txt!")
        
except FileNotFoundError:
    print("  ❌ Arquivo requirements.txt não encontrado!")