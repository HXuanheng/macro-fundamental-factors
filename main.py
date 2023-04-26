import subprocess
import os


def main():
    # If exists remove old pdf file of the paper
    if os.path.exists('main.pdf'):
        os.remove('main.pdf')

    # Change directory to the 'latex' folder
    os.chdir('latex')

    # Compile LaTeX file
    print('Compiling pdf....')
    subprocess.run(["pdflatex", 'main.tex'])
    print('1/3')
    subprocess.run(["bibtex", 'main'])
    print('2/3')
    subprocess.run(["pdflatex", 'main.tex'])
    print('3/3')
    subprocess.run(["pdflatex", 'main.tex'])
    print('Operation Completed')

    # Move the resulting PDF file to the parent directory
    os.rename('main.pdf', '../main.pdf')

    # Change directory back to the parent directory
    os.chdir('..')

if __name__ == '__main__':
    main()
