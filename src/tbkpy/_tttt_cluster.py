class ClusterManager:
    """集群管理器 - 提供简单的集群配置界面"""
    
    def __init__(self):
        self.config = {}
    
    def setup_wizard(self):
        """交互式配置向导"""
        print("TBK集群配置向导")
        
        # 自动发现本地网络
        interfaces = self._discover_network_interfaces()
        print(f"发现网络接口: {interfaces}")
        
        # 简单的问答式配置
        self.config['node_name'] = input("节点名称: ")
        self.config['network'] = self._select_network(interfaces)
        self.config['etcd_endpoint'] = input("ETCD地址 (默认: localhost:2379): ") or "localhost:2379"
        
        return self.config
    
    def save_config(self, path: str = "~/.tbk/config.yaml"):
        """保存配置"""
        # 保存配置到文件
        pass