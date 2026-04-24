using Stride.Engine;

namespace DatasetSandbox
{
    internal static class Program
    {
        public static void Main(string[] args)
        {
            using var game = new DatasetSandboxGame();
            game.Run();
        }
    }
}
