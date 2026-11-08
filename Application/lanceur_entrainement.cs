// Native Windows launcher for the project's existing isolated Python runtime.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

internal static class ForgelyTrainingLauncher
{
    // Windows CommandLineToArgvW quoting, including trailing backslashes.
    private static string Quote(string value)
    {
        StringBuilder result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char character in value)
        {
            if (character == '\\') { slashes++; continue; }
            if (character == '"')
                result.Append('\\', slashes * 2 + 1).Append('"');
            else
                result.Append('\\', slashes).Append(character);
            slashes = 0;
        }
        return result.Append('\\', slashes * 2).Append('"').ToString();
    }

    [STAThread]
    private static int Main(string[] arguments)
    {
        string project = AppDomain.CurrentDomain.BaseDirectory;
        string python = Path.Combine(project, ".venv", "Scripts", "pythonw.exe");
        string script = Path.Combine(project, "Application", "entrainer_forgely.py");
        try
        {
            if (!File.Exists(python) || !File.Exists(script))
                throw new FileNotFoundException("Garde ce lanceur dans le dossier Forgely, avec les dossiers Application et .venv.");
            StringBuilder command = new StringBuilder(Quote(script));
            foreach (string argument in arguments) command.Append(' ').Append(Quote(argument));
            ProcessStartInfo start = new ProcessStartInfo(python, command.ToString());
            start.WorkingDirectory = project;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            using (Process process = Process.Start(start))
            {
                process.WaitForExit();
                return process.ExitCode;
            }
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "Forgely — Entraînement", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
