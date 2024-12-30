import pntos.api as api


def test() -> None:
    assert issubclass(api.StandardInertialMechanization, api.CommonInertial)
    assert issubclass(api.ExternalInertial, api.CommonInertial)
    assert issubclass(
        api.InertialInitializationStrategy, api.CommonInitializationStrategy
    )
    assert issubclass(api.EwcInitializationStrategy, api.CommonInitializationStrategy)


if __name__ == '__main__':
    test()
