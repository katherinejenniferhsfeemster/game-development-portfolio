using System;
using System.IO;
using System.Text.Json;
using Stride.Core.Mathematics;
using Stride.Engine;

namespace DatasetSandbox
{
    /// <summary>
    /// Writes one JSON line per frame with the transform of every named
    /// entity in the scene. Gated on the CAPTURE_PATH env var so normal
    /// editor runs stay quiet.
    /// </summary>
    public class DataCaptureComponent : SyncScript
    {
        public string? CapturePath { get; set; }

        private StreamWriter? _writer;
        private double _t;

        public override void Start()
        {
            if (string.IsNullOrEmpty(CapturePath)) return;
            _writer = new StreamWriter(CapturePath!);
        }

        public override void Update()
        {
            if (_writer == null) return;
            _t += Game.UpdateTime.Elapsed.TotalSeconds;
            foreach (var entity in Entity.Scene.Entities)
            {
                var row = new
                {
                    t = _t,
                    name = entity.Name,
                    pos = new[] { entity.Transform.Position.X, entity.Transform.Position.Y, entity.Transform.Position.Z },
                };
                _writer.WriteLine(JsonSerializer.Serialize(row));
            }
        }

        public override void Cancel()
        {
            _writer?.Flush();
            _writer?.Dispose();
        }
    }
}
