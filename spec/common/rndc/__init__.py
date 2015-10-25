from spec.common.config import cfg
from spec.common.rndc.targets.docker import DockerRndcTarget

CONF = cfg.CONF


def load_rndc_target():
    if CONF.bind.type == 'docker':
        return DockerRndcTarget(
            zone_file_dir=CONF['bind:docker'].dir,
            container_id=CONF['bind:docker'].id,
        )
    else:
        raise Exception("Unable to load bind target-type '%s'"
                        % CONF.bind.type)

if __name__ == '__main__':
    print load_rndc_target()
