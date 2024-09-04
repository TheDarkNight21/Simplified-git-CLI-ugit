ugit - A Simplified Git CLI

Overview

ugit is a custom, lightweight implementation of a version control system inspired by Git. This project simplifies the core functionalities of Git, providing an educational deep dive into how distributed version control systems operate. Though not as feature-rich as Git, ugit covers several essential functionalities, allowing users to track file changes, manage commits, and even work with remote repositories.

By developing ugit, I gained a thorough understanding of Git’s fundamental concepts and the complexities involved in creating command-line tools in Python.

Key Features

	•	Basic Git Commands: ugit supports basic commands like commit, log, branch, and checkout.
	•	File Tracking: Keep track of changes made to files and commit them to the repository.
	•	Branching: Manage branches in your project, switch between them, and merge changes.
	•	Diff and Merge: Compare changes between commits and handle merges effectively.
	•	Remote Repositories: Basic support for pushing and pulling changes to remote repositories.
	•	CLI Built with Python: The entire tool is built in Python, making it a great educational resource for those looking to understand version control or build CLIs.

Project Structure

	•	base.py: Contains foundational functions for handling file management and core utilities.
	•	cli.py: The main entry point for the CLI, handling user input and executing commands.
	•	data.py: Manages data storage, including file changes, commit history, and other repository data.
	•	diff.py: Implements the logic for comparing file changes between commits and handling diffs.
	•	remote.py: Manages interactions with remote repositories, allowing basic push and pull operations.

Setup and Installation

	1.	Clone the repository: git clone https://github.com/yourusername/ugit.git
	2.	Navigate to the project directory: cd ugit
	3.	Install required dependencies: pip install -r requirements.txt
	4.	Run ugit: python cli.py

Usage

Once installed, you can start using ugit by running commands from the CLI:

	•	Commit Changes: python cli.py commit -m “Your commit message”
	•	View Commit Log: python cli.py log
	•	Create a Branch: python cli.py branch 
	•	Checkout a Branch: python cli.py checkout 
	•	Push Changes to Remote: python cli.py push origin 
	•	Pull Changes from Remote: python cli.py pull origin 

Quirks and Important Aspects

	•	Simple Diff Handling: The diff feature in ugit is straightforward, focusing on line-by-line comparisons of file changes.
	•	Basic Remote Management: The current implementation of remote repository support (push/pull) is basic and suitable for small-scale projects. It does not fully support advanced scenarios like conflict resolution.
	•	Branching Simplified: The branching model in ugit is greatly simplified compared to Git, allowing easier understanding of the concepts.
	•	Learning Tool: ugit is designed primarily as a learning tool rather than a production-ready version control system. Its purpose is to help developers understand how Git works internally.

Future Enhancements

	•	Add support for more advanced Git features like stashing and rebasing.
	•	Improve the conflict resolution process when merging branches.
	•	Enhance the remote repository management to support more robust operations.
	•	Build a more extensive set of automated tests for different edge cases.

License

This project is licensed under the MIT License - see the LICENSE file for details.
