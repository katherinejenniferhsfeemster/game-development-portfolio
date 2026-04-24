using System;
using Stride.Engine;
using Stride.Games;

namespace DatasetSandbox
{
    /// <summary>
    /// Main game class. Stride instantiates this via Program.cs; it wires up
    /// a procedurally-populated scene and the dataset capture component.
    /// </summary>
    public class DatasetSandboxGame : Game
    {
        protected override void BeginRun()
        {
            base.BeginRun();

            // Attach a data-capture component to the root scene entity so it
            // receives Update() callbacks each frame.
            var root = new Entity("DataCapture");
            root.Add(new DataCaptureComponent { CapturePath = Environment.GetEnvironmentVariable("CAPTURE_PATH") });
            SceneSystem.SceneInstance.RootScene.Entities.Add(root);
        }
    }
}
