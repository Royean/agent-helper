# AgentLinker
# AI Agent 远程控制系统

cask "agentlinker" do
  version "2.0.0"
  sha256 :no_check  # 需要替换为实际的 SHA256
  
  url "https://github.com/Royean/AgentLinker/releases/latest/download/AgentLinker_macOS.dmg",
      verified: "github.com/Royean/AgentLinker/"
  name "AgentLinker"
  desc "AI Agent Remote Control System"
  homepage "https://github.com/Royean/AgentLinker"
  
  auto_updates true
  
  app "AgentLinker.app"
  
  # 安装后脚本
  postflight do
    system_command "/bin/bash",
      args: [
        "-c",
        "#{appdir}/AgentLinker.app/Contents/Resources/installer/macos/install.sh"
      ],
      sudo: true
  end
  
  # 卸载脚本
  uninstall_postflight do
    system_command "/bin/launchctl",
      args: ["bootout", "system/com.agentlinker.client"],
      sudo: true
  end
  
  uninstall quit: "com.agentlinker.client"
  
  caveats <<~EOS
    AgentLinker has been installed.
    
    To configure:
      1. Edit /etc/agentlinker/config.json
      2. Set your token and server_url
    
    To start the service:
      sudo launchctl start com.agentlinker.client
    
    To view logs:
      tail -f /var/log/agentlinker/agentlinker.log
    
    For more information, visit:
      https://github.com/Royean/AgentLinker
  EOS
end
